"""Local lexical retrieval with page references; no embedding service required."""
from collections import Counter
from math import log
import re
import unicodedata

STOP_WORDS = set("va la cua cac nhung mot trong voi cho nay duoc tu de co khi ve the theo noi dung bai hoc slide tai lieu chuong phan".split())


def tokens(text: str) -> list[str]:
    folded = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    return [word for word in re.findall(r"[a-z0-9_]+", folded) if len(word) > 1 and word not in STOP_WORDS]


def build_chunks(documents, legacy_text: str = "", legacy_name: str | None = None) -> list[dict]:
    chunks = []
    for document in documents:
        for page in document.pages:
            text = page["text"]
            for start in range(0, len(text), 600):
                excerpt = text[start:start + 700].strip()
                if excerpt:
                    chunks.append({"id": f"S{len(chunks) + 1}", "document_id": document.id,
                                   "filename": document.filename, "page": page["page"], "text": excerpt})
    if not chunks and legacy_text:
        for start in range(0, len(legacy_text), 600):
            chunks.append({"id": f"S{len(chunks) + 1}", "document_id": "legacy",
                           "filename": legacy_name or "Tài liệu đã lưu", "page": None,
                           "text": legacy_text[start:start + 700]})
    return chunks


def retrieve(chunks: list[dict], query: str, limit: int = 2400, diverse: bool = False) -> list[dict]:
    if not chunks:
        return []
    wanted = set(tokens(query))
    counts = [Counter(tokens(chunk["text"])) for chunk in chunks]
    frequencies = {term: sum(term in count for count in counts) for term in wanted}
    scores = [sum(log(1 + len(chunks) / (1 + frequencies[term])) * count[term] / (count[term] + 1)
                  for term in wanted) / (1 + sum(count.values()) / 150) for count in counts]
    ranked = sorted(range(len(chunks)), key=lambda i: (-scores[i], i))
    if diverse:
        first, seen = [], set()
        for i in ranked:
            if chunks[i]["document_id"] not in seen:
                first.append(i)
                seen.add(chunks[i]["document_id"])
        ranked = first + [i for i in ranked if i not in first]
    selected, remaining = [], limit
    chunk_limit = min(700, limit // len({chunk["document_id"] for chunk in chunks})) if diverse else 700
    for i in ranked:
        if selected and scores[i] == 0 and not diverse:
            break
        if remaining < (min(150, chunk_limit) if diverse else 150) or len(selected) == (5 if diverse else 4):
            break
        chunk = dict(chunks[i])
        chunk["text"] = chunk["text"][:min(chunk_limit, remaining)]
        selected.append(chunk)
        remaining -= len(chunk["text"])
    return selected


def source_prompt(chunks: list[dict]) -> str:
    return "\n\n".join(f"[{chunk['id']}] {chunk['filename']} · trang {chunk['page'] or 'không phân trang'}\n{chunk['text']}"
                        for chunk in chunks)


def citations(chunks: list[dict], source_ids: list[str]) -> list[dict]:
    allowed = {chunk["id"]: chunk for chunk in chunks}
    if any(source_id not in allowed for source_id in source_ids):
        raise ValueError("Model dẫn nguồn không có trong các đoạn tài liệu được cung cấp.")
    return [{"document_id": allowed[key]["document_id"], "filename": allowed[key]["filename"],
             "page": allowed[key]["page"], "excerpt": allowed[key]["text"]}
            for key in dict.fromkeys(source_ids)]
