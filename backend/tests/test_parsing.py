import pytest
from app.demo import DEMO
from app.ollama import parse_lesson_json, build_messages, OllamaError
from app.parser import extract_document
from app.schemas import LessonContent


def test_demo_schema():
    lesson = LessonContent.model_validate(DEMO)
    assert len(lesson.slides) == 3
    assert lesson.quiz[0].correct_index == 1


def test_markdown_parser():
    assert "Harris" in extract_document("example.md", b"# Harris Corner Detection")


def test_unsupported_file():
    with pytest.raises(ValueError):
        extract_document("notes.exe", b"not allowed")


def test_json_code_fences():
    import json
    text = "```json\n" + json.dumps(DEMO, ensure_ascii=False) + "\n```"
    assert len(parse_lesson_json(text).slides) == 3


def test_bad_json():
    with pytest.raises(OllamaError):
        parse_lesson_json("not json")


def test_source_safety_instruction():
    result = build_messages("Harris", "CV", "sample", 3)
    assert "không đáng tin" in result[0]["content"]


def test_multi_upload_combines_sources():
    import asyncio
    from io import BytesIO
    from fastapi import UploadFile
    from app.parser import read_uploaded_documents, SOURCE_TEXT_LIMIT
    uploads = [
        UploadFile(filename="harris.md", file=BytesIO(b"# Harris Corner Detection")),
        UploadFile(filename="tasks.txt", file=BytesIO(b"Use ANMS for keypoints")),
    ]
    names, combined = asyncio.run(read_uploaded_documents(uploads, 15))
    assert "harris.md" in names and "tasks.txt" in names
    assert "Harris Corner Detection" in combined and "ANMS" in combined
    assert len(combined) <= SOURCE_TEXT_LIMIT


def test_multi_upload_rejects_more_than_five():
    import asyncio
    from io import BytesIO
    from fastapi import HTTPException, UploadFile
    from app.parser import read_uploaded_documents
    uploads = [UploadFile(filename=f"doc{i}.txt", file=BytesIO(b"test")) for i in range(6)]
    with pytest.raises(HTTPException) as exc:
        asyncio.run(read_uploaded_documents(uploads, 15))
    assert exc.value.status_code == 400


def test_multi_upload_preserves_small_file_and_truncates_large():
    import asyncio
    from io import BytesIO
    from fastapi import UploadFile
    from app.parser import read_uploaded_documents, SOURCE_TEXT_LIMIT
    uploads = [
        UploadFile(filename="summary.md", file=BytesIO(b"short header")),
        UploadFile(filename="large.md", file=BytesIO(b"x" * 15000)),
    ]
    names, combined = asyncio.run(read_uploaded_documents(uploads, 15))
    assert "short header" in combined
    assert "[TÀI LIỆU 2:" in combined
    assert len(combined) <= SOURCE_TEXT_LIMIT
