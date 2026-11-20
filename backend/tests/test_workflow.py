import asyncio
import copy
from io import BytesIO
from types import SimpleNamespace

import fitz
import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main, ollama, workflow
from app.db import Base
from app.demo import DEMO
from app.models import Lesson, LessonDocument, LessonWorkspace
from app.parser import extract_pages, read_document_bundle
from app.retrieval import build_chunks, citations, retrieve
from app.workflow import initial_state


OUTLINE = {"summary": "Harris", "slides": [{"title": "Corners", "focus": "Harris corner response"},
                                            {"title": "ANMS", "focus": "Adaptive non maximum suppression"}]}


@pytest.fixture
def database(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(main, "SessionLocal", sessions)
    info = lambda model: {"model": model, "capabilities": ["completion"]}
    monkeypatch.setattr(main, "inspect_model", info)
    monkeypatch.setattr(workflow, "inspect_model", info)
    monkeypatch.setattr(main, "checked_model", lambda model: model)
    jobs = []
    monkeypatch.setattr(main, "run_generation", jobs.append)
    with sessions() as db:
        lesson = Lesson(title="Harris", topic="Harris and ANMS", model="qwen2.5:3b", slide_count=2,
                        status="generating", source_text="old source", source_name="example.pdf")
        db.add(lesson)
        db.flush()
        lesson_id = lesson.id
        db.add(LessonWorkspace(lesson_id=lesson_id, state=initial_state()))
        db.add(LessonDocument(lesson_id=lesson_id, filename="example.pdf", pages=[
            {"page": 1, "text": "Harris corner response detects corners."},
            {"page": 55, "text": "Adaptive non maximum suppression ANMS selects keypoints."}]))
        db.commit()
    yield sessions, lesson_id, TestClient(main.app), jobs
    engine.dispose()


def fake_generation(monkeypatch, fail_at=None):
    calls = []
    monkeypatch.setattr(workflow, "create_outline", lambda *args: copy.deepcopy(OUTLINE))
    def slide(lesson, item, chunks, mode, info):
        calls.append(item["title"])
        if item["title"] == fail_at:
            raise ollama.OllamaError("simulated timeout")
        selected = retrieve(chunks, item["focus"])
        return {"title": item["title"], "key_point": "Explain", "bullets": ["One", "Two"],
                "speaker_notes": "Notes", "sources": citations(selected, [selected[0]["id"]])}
    monkeypatch.setattr(workflow, "create_slide", slide)
    monkeypatch.setattr(workflow, "create_exercises", lambda lesson, slides, mode, info: {
        **copy.deepcopy(DEMO), "slides": copy.deepcopy(slides)})
    return calls


def test_new_upload_keeps_full_text(database):
    sessions, _, client, jobs = database
    text = "Header\n" + "x" * 20000 + "\nIMPORTANT_END"
    response = client.post("/api/lessons", data={"title": "Long notes", "topic": "Important end", "mode": "balanced"},
                           files=[("files", ("notes.md", text.encode(), "text/markdown"))])
    assert response.status_code == 202
    assert response.json()["model"] == "qwen3:4b"
    assert response.json()["workspace"]["mode"] == "balanced"
    with sessions() as db:
        document = db.scalar(select(LessonDocument).where(LessonDocument.lesson_id == response.json()["id"]))
        assert document.pages[0]["text"] == text
        assert len(db.get(Lesson, response.json()["id"]).source_text) <= 8500
    assert jobs == [response.json()["id"]]


def test_all_pdf_pages_and_real_page_numbers():
    with fitz.open() as pdf:
        for number in range(1, 57):
            pdf.new_page().insert_text((72, 72), f"Page {number} Harris")
        pages = extract_pages("long.pdf", pdf.tobytes())
    assert len(pages) == 56
    assert pages[-1]["page"] == 56 and "Page 56" in pages[-1]["text"]


def test_full_bundle_has_no_silent_truncation():
    uploads = [UploadFile(filename="notes.md", file=BytesIO(b"x" * 12000 + b"END"))]
    _, preview, documents = asyncio.run(read_document_bundle(uploads, 15))
    assert len(preview) <= 8500
    assert documents[0]["pages"][0]["text"].endswith("END")


def test_retrieval_finds_late_content_and_citation():
    document = SimpleNamespace(id="doc", filename="long.pdf", pages=[
        {"page": 1, "text": "Introduction " * 1000},
        {"page": 61, "text": "ANMS adaptive non maximum suppression for Harris keypoints"}])
    chunks = build_chunks([document])
    selected = retrieve(chunks, "ANMS adaptive suppression", 1500)
    assert selected[0]["page"] == 61
    assert sum(len(chunk["text"]) for chunk in selected) <= 1500
    refs = citations(selected, [selected[0]["id"]])
    assert refs[0]["document_id"] == "doc" and refs[0]["page"] == 61
    with pytest.raises(ValueError, match="không có"):
        citations(selected, ["invented-source"])


@pytest.mark.parametrize("count", [3, 5])
@pytest.mark.parametrize("limit", [500, 2400])
def test_outline_coverage_uses_multiple_documents(count, limit):
    docs = [SimpleNamespace(id=str(i), filename=f"{i}.md", pages=[{"page": None, "text": "Harris " * 300}]) for i in range(count)]
    selected = retrieve(build_chunks(docs), "Harris", limit=limit, diverse=True)
    assert len({chunk["document_id"] for chunk in selected}) == count
    assert sum(len(chunk["text"]) for chunk in selected) <= limit


def test_review_is_required_then_create_all_parts(database, monkeypatch):
    sessions, lesson_id, client, jobs = database
    calls = fake_generation(monkeypatch)
    workflow.run_workflow(lesson_id, sessions)
    response = client.get(f"/api/lessons/{lesson_id}").json()
    assert response["status"] == "draft" and response["workspace"]["stage"] == "review"
    assert calls == []
    edited = copy.deepcopy(OUTLINE)
    edited["slides"][0]["title"] = "Edited title"
    assert client.put(f"/api/lessons/{lesson_id}/outline", json=edited).status_code == 200
    response = client.post(f"/api/lessons/{lesson_id}/approve", json=edited)
    assert response.status_code == 202 and response.json()["workspace"]["approved"]
    assert jobs == [lesson_id]
    workflow.run_workflow(lesson_id, sessions)
    ready = client.get(f"/api/lessons/{lesson_id}").json()
    assert ready["status"] == "ready" and ready["content"]["slides"][0]["title"] == "Edited title"
    assert len(ready["content"]["quiz"]) == len(ready["content"]["flashcards"]) == 3
    assert ready["workspace"]["completed_slides"] == 2
    assert ready["content"]["slides"][1]["sources"][0]["page"] == 55
    assert ready["workspace"]["elapsed_seconds"] >= 0


def test_failure_preserves_checkpoint_and_resume_skips_finished_slide(database, monkeypatch):
    sessions, lesson_id, client, _ = database
    calls = fake_generation(monkeypatch, fail_at="ANMS")
    workflow.run_workflow(lesson_id, sessions)
    assert client.post(f"/api/lessons/{lesson_id}/approve", json=OUTLINE).status_code == 202
    workflow.run_workflow(lesson_id, sessions)
    failed = client.get(f"/api/lessons/{lesson_id}").json()
    assert failed["status"] == "failed" and failed["workspace"]["completed_slides"] == 1
    assert calls == ["Corners", "ANMS"]
    resumed_calls = fake_generation(monkeypatch)
    assert client.post(f"/api/lessons/{lesson_id}/resume").status_code == 202
    workflow.run_workflow(lesson_id, sessions)
    assert resumed_calls == ["ANMS"]
    assert client.get(f"/api/lessons/{lesson_id}").json()["status"] == "ready"


def test_slide_edit_and_regenerate_preserve_other_parts(database, monkeypatch):
    sessions, lesson_id, client, _ = database
    fake_generation(monkeypatch)
    workflow.run_workflow(lesson_id, sessions)
    client.post(f"/api/lessons/{lesson_id}/approve", json=OUTLINE)
    workflow.run_workflow(lesson_id, sessions)
    before = client.get(f"/api/lessons/{lesson_id}").json()["content"]
    edited = {**before["slides"][0], "title": "Manual edit"}
    response = client.patch(f"/api/lessons/{lesson_id}/slides/0", json=edited)
    assert response.status_code == 200 and response.json()["content"]["slides"][0]["title"] == "Manual edit"
    assert response.json()["content"]["slides"][0]["sources"] == before["slides"][0]["sources"]
    assert client.post(f"/api/lessons/{lesson_id}/slides/0/generate").status_code == 202
    workflow.run_workflow(lesson_id, sessions)
    after = client.get(f"/api/lessons/{lesson_id}").json()["content"]
    assert after["slides"][1] == before["slides"][1]
    assert after["quiz"] == before["quiz"] and after["flashcards"] == before["flashcards"]


def test_state_and_validation_guards(database, monkeypatch):
    sessions, lesson_id, client, _ = database
    assert client.post(f"/api/lessons/{lesson_id}/resume").status_code == 409
    fake_generation(monkeypatch)
    workflow.run_workflow(lesson_id, sessions)
    assert client.post(f"/api/lessons/{lesson_id}/resume").status_code == 409
    wrong_count = {**OUTLINE, "slides": OUTLINE["slides"] + [OUTLINE["slides"][0]]}
    assert client.post(f"/api/lessons/{lesson_id}/approve", json=wrong_count).status_code == 400
    assert client.patch(f"/api/lessons/{lesson_id}/slides/0", json={}).status_code == 422
    assert client.post(f"/api/lessons/{lesson_id}/approve", json=OUTLINE).status_code == 202
    assert client.put(f"/api/lessons/{lesson_id}/outline", json=OUTLINE).status_code == 409
    assert client.post(f"/api/lessons/{lesson_id}/generate").status_code == 409


def test_delete_removes_new_children_only(database, monkeypatch):
    sessions, lesson_id, client, _ = database
    fake_generation(monkeypatch)
    workflow.run_workflow(lesson_id, sessions)
    assert client.delete(f"/api/lessons/{lesson_id}").status_code == 204
    with sessions() as db:
        assert db.get(LessonWorkspace, lesson_id) is None
        assert db.scalar(select(LessonDocument).where(LessonDocument.lesson_id == lesson_id)) is None


def test_exercises_retry_does_not_regenerate_slides(database, monkeypatch):
    sessions, lesson_id, client, _ = database
    fake_generation(monkeypatch)
    workflow.run_workflow(lesson_id, sessions)
    client.post(f"/api/lessons/{lesson_id}/approve", json=OUTLINE)
    def fail(*args):
        raise ollama.OllamaError("quiz timeout")
    monkeypatch.setattr(workflow, "create_exercises", fail)
    workflow.run_workflow(lesson_id, sessions)
    failed = client.get(f"/api/lessons/{lesson_id}").json()
    assert failed["workspace"]["completed_slides"] == 2 and failed["workspace"]["stage"] == "exercises"
    calls = fake_generation(monkeypatch)
    assert client.post(f"/api/lessons/{lesson_id}/resume").status_code == 202
    workflow.run_workflow(lesson_id, sessions)
    assert calls == [] and client.get(f"/api/lessons/{lesson_id}").json()["status"] == "ready"


def test_restart_keeps_durable_slide_checkpoint(database, monkeypatch):
    sessions, lesson_id, client, _ = database
    fake_generation(monkeypatch, fail_at="ANMS")
    workflow.run_workflow(lesson_id, sessions)
    client.post(f"/api/lessons/{lesson_id}/approve", json=OUTLINE)
    workflow.run_workflow(lesson_id, sessions)
    with sessions() as db:
        db.get(Lesson, lesson_id).status = "generating"
        db.commit()
    monkeypatch.setattr(main, "engine", sessions.kw["bind"])
    with TestClient(main.app) as restarted:
        failed = restarted.get(f"/api/lessons/{lesson_id}").json()
        assert failed["status"] == "failed"
        assert failed["workspace"]["completed_slides"] == 1
        assert "khởi động lại" in failed["error"]
    calls = fake_generation(monkeypatch)
    assert client.post(f"/api/lessons/{lesson_id}/resume").status_code == 202
    workflow.run_workflow(lesson_id, sessions)
    assert calls == ["ANMS"]


def test_generated_slide_schema_bounds_and_source_ids(monkeypatch):
    lesson = SimpleNamespace(title="Harris", model="qwen2.5:3b")
    chunks = [{"id": "S1", "document_id": "doc", "filename": "one.md", "page": None, "text": "Harris corners"}]
    def generate(model, schema, instruction, source, mode, num_predict, info):
        assert schema["properties"]["title"]["maxLength"] == 140
        assert schema["properties"]["bullets"]["maxItems"] == 3
        assert num_predict == 1100 and schema["additionalProperties"] is False
        return {"title": "Harris", "key_point": "Corners", "bullets": ["One", "Two"], "speaker_notes": "Notes", "source_ids": ["S1"]}
    monkeypatch.setattr(workflow, "generate_structured", generate)
    slide = workflow.create_slide(lesson, OUTLINE["slides"][0], chunks, "fast", {})
    assert slide["sources"][0]["filename"] == "one.md"
