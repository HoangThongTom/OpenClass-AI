from io import BytesIO
from pathlib import Path
from fastapi import HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool
import fitz

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt"}
SOURCE_TEXT_LIMIT = 8500
MAX_FILES_PER_LESSON = 5
MAX_TOTAL_UPLOAD_MB = 30


def extract_pages(filename: str, raw: bytes) -> list[dict]:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Chỉ hỗ trợ PDF, Markdown (.md) và TXT.")
    if suffix == ".pdf":
        if not raw.startswith(b"%PDF"):
            raise ValueError("Tệp PDF không hợp lệ.")
        try:
            with fitz.open(stream=BytesIO(raw), filetype="pdf") as document:
                if document.needs_pass:
                    raise ValueError("PDF có mật khẩu, vui lòng mở khóa trước.")
                pages = []
                total_chars = 0
                for number, page in enumerate(document, 1):
                    text = page.get_text(sort=True).strip()
                    total_chars += len(text)
                    if total_chars > 2_000_000:
                        raise ValueError("PDF vượt giới hạn 2 triệu ký tự văn bản; hãy chia nhỏ tài liệu.")
                    pages.append({"page": number, "text": text})
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Không thể đọc PDF này.") from exc
    else:
        text = raw.decode("utf-8-sig", errors="replace").strip()
        if len(text) > 2_000_000:
            raise ValueError("Tài liệu vượt giới hạn 2 triệu ký tự văn bản; hãy chia nhỏ tài liệu.")
        pages = [{"page": None, "text": text}]
    if not any(page["text"] for page in pages):
        raise ValueError("Tài liệu không có văn bản để trích xuất. PDF scan cần OCR (chưa hỗ trợ ở MVP).")
    return pages


def extract_document(filename: str, raw: bytes) -> str:
    return "\n".join(page["text"] for page in extract_pages(filename, raw))


async def read_uploaded_document(file: UploadFile, max_mb: int) -> tuple[str, str]:
    filename = Path(file.filename or "document").name
    if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(400, "Chỉ hỗ trợ PDF, Markdown (.md) và TXT.")
    raw = await file.read(max_mb * 1024 * 1024 + 1)
    if len(raw) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"Tệp vượt giới hạn {max_mb} MB.")
    try:
        return filename, extract_document(filename, raw)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


async def read_document_bundle(files: list[UploadFile], max_mb: int) -> tuple[str, str, list[dict]]:
    """Keep full extracted pages; the bounded preview only supports old callers."""
    if len(files) > MAX_FILES_PER_LESSON:
        raise HTTPException(400, f"Chỉ được tải tối đa {MAX_FILES_PER_LESSON} tài liệu mỗi bài học.")
    if not files:
        return "", "", []

    names: list[str] = []
    texts: list[str] = []
    documents: list[dict] = []
    total_chars = 0
    total_size = 0
    for file in files:
        filename = (file.filename or "document").replace("\\", "/").split("/")[-1]
        if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise HTTPException(400, f"{filename}: chỉ hỗ trợ PDF, Markdown (.md) và TXT.")
        raw = await file.read(max_mb * 1024 * 1024 + 1)
        if len(raw) > max_mb * 1024 * 1024:
            raise HTTPException(413, f"{filename} vượt giới hạn {max_mb} MB/tệp.")
        total_size += len(raw)
        if total_size > MAX_TOTAL_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"Tổng tài liệu vượt {MAX_TOTAL_UPLOAD_MB} MB.")
        try:
            pages = await run_in_threadpool(extract_pages, filename, raw)
            text = "\n".join(page["text"] for page in pages)
        except ValueError as exc:
            raise HTTPException(400, f"{filename}: {exc}") from exc
        total_chars += len(text)
        if total_chars > 5_000_000:
            raise HTTPException(413, "Tổng văn bản vượt 5 triệu ký tự; hãy chia thành nhiều bài học.")
        documents.append({"filename": filename[:255], "pages": pages})
        names.append(filename)
        texts.append(text)

    headers = [f"[TÀI LIỆU {i + 1}: {name[:90]}]\n" for i, name in enumerate(names)]
    separator = "\n\n"
    budget = max(0, SOURCE_TEXT_LIMIT - sum(map(len, headers)) - len(separator) * (len(files) - 1))
    lengths = [min(len(text), budget // len(files)) for text in texts]
    remaining = budget - sum(lengths)
    for i, text in enumerate(texts):
        additional = min(len(text) - lengths[i], remaining)
        lengths[i] += additional
        remaining -= additional
    combined = separator.join(header + text[:length] for header, text, length in zip(headers, texts, lengths))
    source_names = ", ".join(names)
    return source_names[:255], combined, documents


async def read_uploaded_documents(files: list[UploadFile], max_mb: int) -> tuple[str, str]:
    names, preview, _ = await read_document_bundle(files, max_mb)
    return names, preview
