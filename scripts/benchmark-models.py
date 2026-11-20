"""Compare the real local workflow without writing to the user's PostgreSQL."""
import json
import logging
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models import Lesson, LessonDocument, LessonWorkspace
from app.workflow import initial_state, run_workflow

logging.basicConfig(level=logging.INFO)
root = Path(__file__).resolve().parents[1]
source = (root / "examples" / "harris-corner-detection.md").read_text(encoding="utf-8")
engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
sessions = sessionmaker(bind=engine, expire_on_commit=False)
results = []
for model, mode in (("qwen2.5:3b", "fast"), ("qwen3:4b", "balanced")):
    with sessions() as db:
        lesson = Lesson(title="Harris Corner Detection", topic="Nguyên lý, vùng phẳng/cạnh/góc, công thức và ví dụ",
                        model=model, slide_count=4, status="generating", source_text=source[:8500])
        db.add(lesson)
        db.flush()
        lesson_id = lesson.id
        db.add(LessonWorkspace(lesson_id=lesson_id, state=initial_state(mode)))
        db.add(LessonDocument(lesson_id=lesson_id, filename="harris-corner-detection.md",
                              pages=[{"page": None, "text": source}]))
        db.commit()
    started = perf_counter()
    run_workflow(lesson_id, sessions)
    with sessions() as db:
        lesson = db.get(Lesson, lesson_id)
        workspace = db.get(LessonWorkspace, lesson_id)
        if lesson.status == "draft":
            workspace.state = {**workspace.state, "approved": True, "stage": "slide:1"}
            lesson.status = "generating"
            db.commit()
    run_workflow(lesson_id, sessions)
    with sessions() as db:
        lesson = db.get(Lesson, lesson_id)
        content = lesson.content or {}
        result = {"model": model, "mode": mode, "status": lesson.status,
                  "elapsed_seconds": round(perf_counter() - started, 2),
                  "slides": len(content.get("slides", [])), "quiz": len(content.get("quiz", [])),
                  "flashcards": len(content.get("flashcards", [])),
                  "cited_slides": sum(bool(slide.get("sources")) for slide in content.get("slides", [])),
                  "error": lesson.error}
        results.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
report = root / "reports" / "local-model-benchmark.json"
report.parent.mkdir(exist_ok=True)
report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
engine.dispose()
sys.exit(0 if all(result["status"] == "ready" for result in results) else 1)
