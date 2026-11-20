import logging
from time import perf_counter
from .db import SessionLocal
from .models import Lesson, LessonWorkspace
from .ollama import generate_lesson
from .workflow import run_workflow

log = logging.getLogger(__name__)


def run_generation(lesson_id: str) -> None:
    """MVP process-local background job. Must run with a single API worker."""
    with SessionLocal() as db:
        has_workspace = db.get(LessonWorkspace, lesson_id) is not None
    if has_workspace:
        run_workflow(lesson_id, SessionLocal)
        return
    with SessionLocal() as db:
        lesson = db.get(Lesson, lesson_id)
        if lesson is None:
            return
        started = perf_counter()
        log.info("Generation start lesson_id=%s model=%s slides=%d source_chars=%d", lesson_id, lesson.model, lesson.slide_count, len(lesson.source_text))
        try:
            content = generate_lesson(
                title=lesson.title,
                topic=lesson.topic,
                source_text=lesson.source_text,
                model=lesson.model,
                slide_count=lesson.slide_count,
            )
            lesson.content = content.model_dump(mode="json")
            lesson.status = "ready"
            lesson.error = None
        except Exception as exc:
            log.exception("Generation failed for %s", lesson_id)
            lesson.status = "failed"
            lesson.error = str(exc)[:1200]
        db.commit()
        log.info("Generation finished lesson_id=%s model=%s status=%s elapsed_s=%.2f", lesson_id, lesson.model, lesson.status, perf_counter() - started)
