from contextlib import asynccontextmanager
import copy
import logging
from typing import Literal
from fastapi import BackgroundTasks, Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from sqlalchemy import delete, select, text
from .config import get_settings
from .db import Base, SessionLocal, engine
from .demo import DEMO
from .generation import run_generation
from .models import Lesson, LessonDocument, LessonWorkspace
from .ollama import OllamaError, inspect_model, list_models, require_model
from .parser import read_document_bundle
from .schemas import LessonContent, LessonOut, ModelList, OutlineContent, RegenerateLesson, SlideEdit, WorkspaceOut
from .workflow import initial_state

logging.basicConfig(level=logging.INFO)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # A previous process may have been closed mid-generation.
    with SessionLocal() as db:
        interrupted = db.execute(select(Lesson).where(Lesson.status == "generating")).scalars().all()
        for lesson in interrupted:
            lesson.status = "failed"
            lesson.error = "Server đã khởi động lại khi đang tạo. Hãy nhấn 'Tạo lại'."
        db.commit()
    yield


app = FastAPI(title="OpenClass AI API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://127.0.0.1:3002"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    try:
        models = list_models()
        return {"api": "online", "database": "online", "ollama": "online", "models": models}
    except Exception:
        return {"api": "online", "database": "online", "ollama": "offline", "models": []}


@app.get("/api/models", response_model=ModelList)
def models():
    try:
        return ModelList(online=True, models=list_models())
    except OllamaError as exc:
        return ModelList(online=False, models=[], error=str(exc))


def checked_model(model: str) -> str:
    try:
        return require_model(model)
    except OllamaError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


@app.get("/api/model-info")
def model_info(model: str):
    try:
        return inspect_model(model)
    except OllamaError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


def lesson_output(db, lesson) -> LessonOut:
    result = LessonOut.model_validate(lesson)
    workspace = db.get(LessonWorkspace, lesson.id)
    if workspace:
        result.workspace = WorkspaceOut.model_validate(workspace.state)
    return result


def get_editable(db, lesson_id: str):
    lesson = db.scalar(select(Lesson).where(Lesson.id == lesson_id).with_for_update())
    if lesson is None:
        raise HTTPException(404, "Không tìm thấy bài học.")
    if lesson.status == "generating":
        raise HTTPException(409, "Bài học đang được tạo.")
    return lesson


def source_warning(db, lesson) -> str | None:
    if lesson.source_text and not db.scalar(select(LessonDocument.id).where(LessonDocument.lesson_id == lesson.id).limit(1)):
        return "Bài cũ chỉ còn đoạn trích đã lưu, không có số trang gốc. Tạo bài mới với file gốc để sử dụng đầy đủ tài liệu."
    return None


@app.get("/api/lessons", response_model=list[LessonOut])
def get_lessons():
    with SessionLocal() as db:
        rows = db.execute(select(Lesson).order_by(Lesson.created_at.desc()).limit(100)).scalars().all()
        return [lesson_output(db, row) for row in rows]


@app.get("/api/lessons/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: str):
    with SessionLocal() as db:
        lesson = db.get(Lesson, lesson_id)
        if lesson is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài học.")
        return lesson_output(db, lesson)


@app.post("/api/lessons", response_model=LessonOut, status_code=202)
async def create_lesson(
    background_tasks: BackgroundTasks,
    title: str = Form(..., min_length=3, max_length=180),
    topic: str = Form(..., min_length=3, max_length=1500),
    model: str = Form(default="", max_length=150),
    slide_count: int = Form(default=3, ge=2, le=6),
    mode: Literal["fast", "balanced"] = Form(default="fast"),
    files: list[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),  # backward compatibility with MVP v0.1
):
    title, topic = title.strip(), topic.strip()
    if not title or not topic:
        raise HTTPException(400, "Tiêu đề và chủ đề không được để trống.")
    selected = model.strip() or ("qwen3:4b" if mode == "balanced" else settings.default_ollama_model)
    model = await run_in_threadpool(checked_model, selected)
    await run_in_threadpool(model_info, model)
    name, source_text = None, ""
    uploads = [item for item in (files or []) if item.filename]
    if file is not None and file.filename:
        uploads.append(file)
    documents = []
    if uploads:
        name, source_text, documents = await read_document_bundle(uploads, settings.max_upload_mb)
    with SessionLocal() as db:
        lesson = Lesson(
            title=title,
            topic=topic,
            model=model,
            slide_count=slide_count,
            source_name=name,
            source_text=source_text,
            status="generating",
        )
        db.add(lesson)
        db.flush()
        db.add(LessonWorkspace(lesson_id=lesson.id, state=initial_state(mode)))
        for document in documents:
            db.add(LessonDocument(lesson_id=lesson.id, **document))
        db.commit()
        output = lesson_output(db, lesson)
    background_tasks.add_task(run_generation, output.id)
    return output


@app.post("/api/lessons/{lesson_id}/generate", response_model=LessonOut, status_code=202)
def retry_generation(lesson_id: str, background_tasks: BackgroundTasks, options: RegenerateLesson | None = Body(default=None)):
    with SessionLocal() as db:
        lesson = get_editable(db, lesson_id)
        model = checked_model(options.model if options and options.model is not None else lesson.model)
        model_info(model)
        lesson.model = model
        if options and options.slide_count is not None:
            lesson.slide_count = options.slide_count
        lesson.status = "generating"
        lesson.error = None
        workspace = db.get(LessonWorkspace, lesson_id)
        mode = options.mode if options and options.mode else (workspace.state["mode"] if workspace else "fast")
        state = initial_state(mode, source_warning(db, lesson))
        if workspace:
            workspace.state = state
        else:
            db.add(LessonWorkspace(lesson_id=lesson_id, state=state))
        db.commit()
        db.refresh(lesson)
        output = lesson_output(db, lesson)
    background_tasks.add_task(run_generation, lesson_id)
    return output


@app.put("/api/lessons/{lesson_id}/outline", response_model=LessonOut)
def save_outline(lesson_id: str, outline: OutlineContent):
    with SessionLocal() as db:
        lesson = get_editable(db, lesson_id)
        workspace = db.get(LessonWorkspace, lesson_id)
        if not workspace or workspace.state["approved"] or not workspace.state.get("outline"):
            raise HTTPException(409, "Hãy tạo dàn ý mới trước khi chỉnh sửa.")
        if len(outline.slides) != lesson.slide_count:
            raise HTTPException(400, f"Dàn ý cần đúng {lesson.slide_count} slide.")
        state = copy.deepcopy(workspace.state)
        state.update(outline=outline.model_dump(), stage="review")
        workspace.state = state
        lesson.status, lesson.error = "draft", None
        db.commit()
        return lesson_output(db, lesson)


@app.post("/api/lessons/{lesson_id}/approve", response_model=LessonOut, status_code=202)
def approve_outline(lesson_id: str, outline: OutlineContent, background_tasks: BackgroundTasks):
    save_outline(lesson_id, outline)
    with SessionLocal() as db:
        lesson = get_editable(db, lesson_id)
        workspace = db.get(LessonWorkspace, lesson_id)
        state = copy.deepcopy(workspace.state)
        state.update(approved=True, stage="slide:1", draft={"slides": []}, completed_slides=0)
        workspace.state = state
        lesson.status, lesson.error = "generating", None
        db.commit()
        output = lesson_output(db, lesson)
    background_tasks.add_task(run_generation, lesson_id)
    return output


@app.post("/api/lessons/{lesson_id}/resume", response_model=LessonOut, status_code=202)
def resume_generation(lesson_id: str, background_tasks: BackgroundTasks):
    with SessionLocal() as db:
        lesson = get_editable(db, lesson_id)
        workspace = db.get(LessonWorkspace, lesson_id)
        if lesson.status != "failed" or not workspace:
            raise HTTPException(409, "Chỉ có thể tiếp tục bài tạo lỗi đã lưu tiến độ.")
        model_info(lesson.model)
        lesson.status, lesson.error = "generating", None
        db.commit()
        output = lesson_output(db, lesson)
    background_tasks.add_task(run_generation, lesson_id)
    return output


@app.patch("/api/lessons/{lesson_id}/slides/{index}", response_model=LessonOut)
def edit_slide(lesson_id: str, index: int, slide: SlideEdit):
    with SessionLocal() as db:
        lesson = get_editable(db, lesson_id)
        if lesson.status != "ready":
            raise HTTPException(409, "Chỉ chỉnh sửa slide khi bài học đã sẵn sàng.")
        if not lesson.content or not 0 <= index < len(lesson.content["slides"]):
            raise HTTPException(404, "Không tìm thấy slide.")
        if not slide.title.strip() or not slide.key_point.strip() or any(not bullet.strip() for bullet in slide.bullets):
            raise HTTPException(400, "Tiêu đề, ý chính và các gạch đầu dòng không được để trống.")
        content = copy.deepcopy(lesson.content)
        content["slides"][index] = {**slide.model_dump(), "sources": content["slides"][index].get("sources", [])}
        lesson.content = content
        workspace = db.get(LessonWorkspace, lesson_id)
        if workspace and workspace.state["stage"] == "ready":
            state = copy.deepcopy(workspace.state)
            state["draft"] = content
            if state.get("outline"):
                state["outline"]["slides"][index] = {"title": slide.title, "focus": slide.key_point}
            workspace.state = state
        db.commit()
        return lesson_output(db, lesson)


@app.post("/api/lessons/{lesson_id}/slides/{index}/generate", response_model=LessonOut, status_code=202)
def regenerate_slide(lesson_id: str, index: int, background_tasks: BackgroundTasks):
    with SessionLocal() as db:
        lesson = get_editable(db, lesson_id)
        if lesson.status != "ready" or not lesson.content or not 0 <= index < len(lesson.content["slides"]):
            raise HTTPException(409, "Cần bài học sẵn sàng và slide hợp lệ để tạo lại.")
        model_info(lesson.model)
        workspace = db.get(LessonWorkspace, lesson_id)
        state = copy.deepcopy(workspace.state) if workspace else initial_state(source_warning=source_warning(db, lesson))
        if not state.get("outline"):
            state["outline"] = {"summary": lesson.content["summary"], "slides": [
                {"title": slide["title"], "focus": slide["key_point"]} for slide in lesson.content["slides"]]}
        state.update(approved=True, stage=f"slide:{index + 1}", target_slide=index)
        if workspace:
            workspace.state = state
        else:
            db.add(LessonWorkspace(lesson_id=lesson_id, state=state))
        lesson.status, lesson.error = "generating", None
        db.commit()
        output = lesson_output(db, lesson)
    background_tasks.add_task(run_generation, lesson_id)
    return output


@app.delete("/api/lessons/{lesson_id}", status_code=204)
def delete_lesson(lesson_id: str):
    with SessionLocal() as db:
        lesson = db.get(Lesson, lesson_id)
        if lesson is None:
            raise HTTPException(404, "Không tìm thấy bài học.")
        if lesson.status == "generating":
            raise HTTPException(409, "Không thể xóa khi đang tạo.")
        db.execute(delete(LessonDocument).where(LessonDocument.lesson_id == lesson_id))
        db.execute(delete(LessonWorkspace).where(LessonWorkspace.lesson_id == lesson_id))
        db.delete(lesson)
        db.commit()


@app.post("/api/demo", response_model=LessonOut, status_code=201)
def create_demo():
    content = LessonContent.model_validate(DEMO)
    with SessionLocal() as db:
        lesson = Lesson(
            title="Harris Corner Detection — Bài học mẫu",
            topic="Computer Vision: Harris Corner Detection",
            model="demo:offline",
            slide_count=3,
            source_name=None,
            source_text="",
            content=content.model_dump(mode="json"),
            status="ready",
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return LessonOut.model_validate(lesson)
