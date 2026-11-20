import copy
import logging

import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import generation, main, ollama
from app.db import Base
from app.demo import DEMO
from app.models import Lesson
from app.schemas import LessonContent


@pytest.fixture
def api_db(monkeypatch):
    # All API/worker writes stay in an isolated in-memory DB, never PostgreSQL.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(main, "SessionLocal", sessions)
    monkeypatch.setattr(generation, "SessionLocal", sessions)
    monkeypatch.setattr(ollama, "list_models", lambda: ["qwen2.5:3b", "mistral:latest"])
    monkeypatch.setattr(main, "inspect_model", lambda model: {"model": model, "capabilities": ["completion"]})
    jobs = []
    monkeypatch.setattr(main, "run_generation", jobs.append)
    with sessions() as db:
        lesson = Lesson(title="Harris", topic="Corners", model="mistral:latest", slide_count=4,
                        status="failed", error="old timeout", source_text="original source",
                        source_name="one.pdf, two.md", content=copy.deepcopy(DEMO))
        db.add(lesson)
        db.commit()
        lesson_id = lesson.id
    # No production lifespan: it initializes/reconciles the real DB on startup.
    yield TestClient(main.app), sessions, lesson_id, jobs
    engine.dispose()


def test_retry_saves_new_options_preserves_documents_and_content(api_db):
    client, sessions, lesson_id, jobs = api_db
    response = client.post(f"/api/lessons/{lesson_id}/generate", json={"model": "qwen2.5:3b", "slide_count": 2})
    assert response.status_code == 202
    assert response.json()["model"] == "qwen2.5:3b"
    assert response.json()["slide_count"] == 2
    assert jobs == [lesson_id]
    with sessions() as db:
        lesson = db.get(Lesson, lesson_id)
        assert lesson.status == "generating" and lesson.error is None
        assert lesson.source_text == "original source"
        assert lesson.source_name == "one.pdf, two.md"
        assert lesson.content == DEMO


@pytest.mark.parametrize("body, expected_model, expected_count", [
    (None, "mistral:latest", 4),
    ({"model": "qwen2.5:3b"}, "qwen2.5:3b", 4),
    ({"slide_count": 3}, "mistral:latest", 3),
])
def test_retry_backwards_compatibility(api_db, body, expected_model, expected_count):
    client, _, lesson_id, _ = api_db
    response = client.post(f"/api/lessons/{lesson_id}/generate", **({"json": body} if body else {}))
    assert response.status_code == 202
    assert response.json()["model"] == expected_model
    assert response.json()["slide_count"] == expected_count


@pytest.mark.parametrize("body", [{"slide_count": 1}, {"slide_count": 7}, {"model": ""}])
def test_retry_invalid_options(api_db, body):
    client, _, lesson_id, jobs = api_db
    assert client.post(f"/api/lessons/{lesson_id}/generate", json=body).status_code == 422
    assert jobs == []


def test_missing_model_does_not_mutate_lesson(api_db):
    client, sessions, lesson_id, jobs = api_db
    response = client.post(f"/api/lessons/{lesson_id}/generate", json={"model": "missing:3b"})
    assert response.status_code == 400 and "chưa có" in response.json()["detail"]
    with sessions() as db:
        lesson = db.get(Lesson, lesson_id)
        assert lesson.model == "mistral:latest" and lesson.status == "failed"
        assert lesson.error == "old timeout"
    assert jobs == []


def test_create_with_pdf_and_markdown(api_db):
    client, sessions, _, jobs = api_db
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "Harris corner detection")
        raw = pdf.tobytes()
    response = client.post("/api/lessons", data={
        "title": "Harris", "topic": "Corners", "model": "qwen2.5:3b", "slide_count": "4",
    }, files=[("files", ("one.pdf", raw, "application/pdf")),
              ("files", ("two.md", b"# ANMS", "text/markdown"))])
    assert response.status_code == 202
    assert response.json()["model"] == "qwen2.5:3b"
    with sessions() as db:
        lesson = db.get(Lesson, response.json()["id"])
        assert "Harris corner" in lesson.source_text and "ANMS" in lesson.source_text
        assert lesson.source_name == "one.pdf, two.md"
    assert jobs == [response.json()["id"]]


def test_create_missing_model_and_offline_do_not_insert(api_db, monkeypatch):
    client, sessions, _, jobs = api_db
    data = {"title": "Harris", "topic": "Corners", "model": "missing:3b"}
    assert client.post("/api/lessons", data=data).status_code == 400
    def offline():
        raise ollama.OllamaError("Ollama offline", 503)
    monkeypatch.setattr(ollama, "list_models", offline)
    assert client.post("/api/lessons", data=data).status_code == 503
    with sessions() as db:
        assert len(db.scalars(select(Lesson)).all()) == 1
    assert jobs == []


def test_retry_busy_and_not_found(api_db):
    client, sessions, lesson_id, _ = api_db
    assert client.post("/api/lessons/missing/generate").status_code == 404
    with sessions() as db:
        db.get(Lesson, lesson_id).status = "generating"
        db.commit()
    assert client.post(f"/api/lessons/{lesson_id}/generate").status_code == 409


@pytest.mark.parametrize("fails", [False, True])
def test_worker_status_error_and_timing(api_db, monkeypatch, caplog, fails):
    _, sessions, lesson_id, _ = api_db
    def generate(**kwargs):
        assert kwargs["source_text"] == "original source"
        if fails:
            raise ollama.OllamaError("Ollama timeout: model mistral:latest")
        return LessonContent.model_validate(DEMO)
    monkeypatch.setattr(generation, "generate_lesson", generate)
    with caplog.at_level(logging.INFO):
        generation.run_generation(lesson_id)
    with sessions() as db:
        lesson = db.get(Lesson, lesson_id)
        assert lesson.status == ("failed" if fails else "ready")
        assert ("mistral:latest" in lesson.error) if fails else lesson.error is None
        assert lesson.content == (DEMO if fails else LessonContent.model_validate(DEMO).model_dump(mode="json"))
    assert "elapsed_s=" in caplog.text and lesson_id in caplog.text
