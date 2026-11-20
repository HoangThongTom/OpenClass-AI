"""Outline review and incremental generation, persisted after every step."""
import copy
import logging
from threading import Lock
from time import perf_counter

from sqlalchemy import select
from .config import get_settings
from .models import Lesson, LessonDocument, LessonWorkspace
from .ollama import generate_structured, inspect_model, OllamaError
from .retrieval import build_chunks, citations, retrieve, source_prompt
from .schemas import LessonContent, OutlineContent, Slide, SlideEdit

log = logging.getLogger(__name__)
generation_lock = Lock()


def initial_state(mode: str = "fast", source_warning: str | None = None) -> dict:
    return {"mode": mode, "stage": "outline", "outline": None, "approved": False,
            "completed_slides": 0, "elapsed_seconds": 0, "last_run_seconds": 0,
            "source_warning": source_warning, "draft": {"slides": []}, "target_slide": None}


def exact_array(schema: dict, key: str, count: int) -> dict:
    schema["properties"][key].update(minItems=count, maxItems=count)
    return schema


def create_outline(lesson, chunks: list[dict], mode: str, info: dict) -> dict:
    selected = retrieve(chunks, lesson.title + " " + lesson.topic,
                        limit=get_settings().ollama_source_char_limit, diverse=True)
    schema = exact_array(OutlineContent.model_json_schema(), "slides", lesson.slide_count)
    schema["additionalProperties"] = False
    schema["properties"]["summary"]["maxLength"] = 300
    schema["$defs"]["OutlineItem"]["additionalProperties"] = False
    schema["$defs"]["OutlineItem"]["properties"]["title"]["maxLength"] = 100
    schema["$defs"]["OutlineItem"]["properties"]["focus"]["maxLength"] = 180
    raw = generate_structured(lesson.model, schema,
                              f"Lập dàn ý đúng {lesson.slide_count} slide cho {lesson.title}. Chủ đề: {lesson.topic}. "
                              "summary 1 câu; mỗi slide có title dưới 10 từ, focus 1 câu mô tả nội dung cần dạy.",
                              source_prompt(selected), mode, 1000, info)
    outline = OutlineContent.model_validate(raw)
    if len(outline.slides) != lesson.slide_count:
        raise OllamaError("Model trả sai số mục dàn ý. Hãy thử tạo dàn ý lại.")
    return outline.model_dump()


def create_slide(lesson, item: dict, chunks: list[dict], mode: str, info: dict) -> dict:
    selected = retrieve(chunks, item["title"] + " " + item["focus"],
                        limit=min(2200, get_settings().ollama_source_char_limit))
    schema = SlideEdit.model_json_schema()
    for key, length in (("title", 140), ("key_point", 300), ("speaker_notes", 500)):
        schema["properties"][key]["maxLength"] = length
    schema["properties"]["bullets"].update(minItems=2, maxItems=3)
    schema["properties"]["bullets"]["items"]["maxLength"] = 180
    schema["additionalProperties"] = False
    schema["properties"]["source_ids"] = {"type": "array", "items": {"type": "string", "enum": [chunk["id"] for chunk in selected]} if selected else {"type": "string"},
                                         "minItems": 1 if selected else 0, "maxItems": min(4, len(selected))}
    schema["required"] = list(schema["properties"])
    raw = generate_structured(lesson.model, schema,
                              f"Soạn một slide của bài {lesson.title}. Tiêu đề: {item['title']}. "
                              f"Nội dung cần dạy: {item['focus']}. "
                              "Giữ ý của tiêu đề đã duyệt. key_point 1 câu, bullets 2–3 ý dưới 20 từ, "
                              "speaker_notes 1–2 câu. source_ids chỉ chứa ID các đoạn thực sự dùng, "
                              "ví dụ S1; để [] nếu không có tài liệu. Không tự tạo ID.",
                              source_prompt(selected), mode, 1400 if mode == "balanced" else 1100, info)
    raw["sources"] = citations(selected, raw.pop("source_ids", []))
    if selected and not raw["sources"]:
        raise OllamaError("Slide chưa chỉ rõ đoạn tài liệu được sử dụng. Hãy tiếp tục để tạo lại phần này.")
    return Slide.model_validate(raw).model_dump()


def create_exercises(lesson, slides: list[dict], mode: str, info: dict) -> dict:
    schema = LessonContent.model_json_schema()
    schema["properties"].pop("slides")
    schema["required"] = ["summary", "quiz", "flashcards"]
    exact_array(schema, "quiz", 3)
    exact_array(schema, "flashcards", 3)
    material = "\n".join(f"{slide['title'][:100]}: {slide['key_point'][:180]} "
                         + "; ".join(bullet[:100] for bullet in slide["bullets"]) for slide in slides)
    raw = generate_structured(lesson.model, schema,
                              "Từ các slide bên dưới, viết summary 1 câu, đúng 3 câu quiz (4 lựa chọn, "
                              "correct_index từ 0 đến 3, explanation ngắn) và đúng 3 flashcards front/back. "
                              "Không tạo trường slides. Câu hỏi ngắn, đáp án dưới 8 từ.",
                              material[:3500], mode, 1800, info)
    content = LessonContent.model_validate({**raw, "slides": slides})
    if len(content.quiz) != 3 or len(content.flashcards) != 3:
        raise OllamaError("Quiz/flashcards chưa đủ. Các slide đã được lưu; hãy tiếp tục phần ôn tập.")
    return content.model_dump(mode="json")


def run_workflow(lesson_id: str, sessions) -> None:
    # One active local model request at a time on a 4 GB GPU. DB checkpoints survive restarts.
    with generation_lock, sessions() as db:
        lesson = db.get(Lesson, lesson_id)
        workspace = db.get(LessonWorkspace, lesson_id)
        if lesson is None or workspace is None or lesson.status != "generating":
            return
        state = copy.deepcopy(workspace.state)
        started = perf_counter()
        def checkpoint():
            state["last_run_seconds"] = round(perf_counter() - started, 2)
            workspace.state = copy.deepcopy(state)
            db.commit()
        try:
            info = inspect_model(lesson.model)
            documents = db.scalars(select(LessonDocument).where(LessonDocument.lesson_id == lesson_id)).all()
            chunks = build_chunks(documents, lesson.source_text, lesson.source_name)
            mode = state["mode"]
            if not state["approved"]:
                state["outline"] = create_outline(lesson, chunks, mode, info)
                state["stage"] = "review"
                lesson.status = "draft"
            elif state.get("target_slide") is not None:
                index = state["target_slide"]
                slide = create_slide(lesson, state["outline"]["slides"][index], chunks, mode, info)
                content = copy.deepcopy(lesson.content)
                content["slides"][index] = slide
                lesson.content = content
                state["draft"] = content
                state["target_slide"] = None
                state["stage"] = "ready"
                lesson.status = "ready"
            else:
                draft = state["draft"]
                for index in range(len(draft["slides"]), lesson.slide_count):
                    state["stage"] = f"slide:{index + 1}"
                    checkpoint()
                    draft["slides"].append(create_slide(lesson, state["outline"]["slides"][index], chunks, mode, info))
                    state["completed_slides"] = len(draft["slides"])
                    checkpoint()
                state["stage"] = "exercises"
                checkpoint()
                content = create_exercises(lesson, draft["slides"], mode, info)
                lesson.content = content
                state["draft"] = content
                state["stage"] = "ready"
                lesson.status = "ready"
            lesson.error = None
        except Exception as exc:
            log.exception("Workflow failed lesson_id=%s stage=%s model=%s", lesson_id, state["stage"], lesson.model)
            lesson.status = "failed"
            lesson.error = str(exc)[:1200]
        finally:
            state["elapsed_seconds"] += round(perf_counter() - started, 2)
            checkpoint()
            log.info("Workflow finished lesson_id=%s model=%s stage=%s status=%s elapsed_s=%.2f",
                     lesson_id, lesson.model, state["stage"], lesson.status, perf_counter() - started)
