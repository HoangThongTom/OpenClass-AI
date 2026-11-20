import copy
import json
import logging

import httpx
import pytest

from app import ollama
from app.config import Settings
from app.demo import DEMO


@pytest.fixture
def ollama_server(monkeypatch):
    settings = Settings(_env_file=None)
    monkeypatch.setattr(ollama, "get_settings", lambda: settings)
    original_client = httpx.Client
    requests = []

    def install(chat=None, tags=None, info=None):
        def handler(request):
            requests.append(request)
            if request.url.path == "/api/tags":
                return httpx.Response(200, json=tags if tags is not None else {
                    "models": [{"name": "qwen2.5:3b"}, {"name": "mistral:latest"}],
                })
            if request.url.path == "/api/show":
                return httpx.Response(200, json=info if info is not None else {"capabilities": ["completion"]})
            if isinstance(chat, Exception):
                raise chat
            return httpx.Response(200, json=chat if chat is not None else {
                "message": {"content": json.dumps(DEMO)}, "done_reason": "stop",
                "total_duration": 3_000_000_000, "load_duration": 1_000_000_000,
                "prompt_eval_duration": 500_000_000, "eval_duration": 1_500_000_000,
                "prompt_eval_count": 400, "eval_count": 900,
            })

        monkeypatch.setattr(ollama.httpx, "Client", lambda **kwargs: original_client(
            transport=httpx.MockTransport(handler), **kwargs,
        ))
        return requests

    return install


def test_small_model_request_and_metrics(ollama_server, caplog):
    requests = ollama_server()
    source = "[TÀI LIỆU 1: long.pdf]\n" + "Harris " * 900 + "\n\n[TÀI LIỆU 2: short.md]\nANMS"
    with caplog.at_level(logging.INFO):
        content = ollama.generate_lesson("Harris", "Corners", source, "qwen2.5:3b", 3)
    assert len(content.quiz) == len(content.flashcards) == 3
    assert requests[0].url.path == "/api/tags"
    payload = json.loads(requests[-1].content)
    assert payload["model"] == "qwen2.5:3b"
    assert payload["options"]["num_ctx"] == 4096
    assert payload["options"]["num_predict"] == 1600
    assert payload["stream"] is False
    assert payload["format"]["required"] == ["summary", "slides", "quiz", "flashcards"]
    for key in ("slides", "quiz", "flashcards"):
        assert payload["format"]["properties"][key]["minItems"] == 3
        assert payload["format"]["properties"][key]["maxItems"] == 3
    assert "ANMS" in payload["messages"][1]["content"]
    assert "load_s=1.00" in caplog.text and "elapsed_s=" in caplog.text
    assert "Harris Corners" not in caplog.text


def test_four_slide_budget_and_counts(ollama_server):
    demo = copy.deepcopy(DEMO)
    demo["slides"].append(copy.deepcopy(demo["slides"][0]))
    requests = ollama_server(chat={"message": {"content": json.dumps(demo)}})
    assert len(ollama.generate_lesson("Harris", "Corners", "", "qwen2.5:3b", 4).slides) == 4
    assert json.loads(requests[-1].content)["options"]["num_predict"] == 1900


@pytest.mark.parametrize("limit", [0, 500, 2400])
def test_excerpt_preserves_each_document(limit):
    source = "[TÀI LIỆU 1: big.pdf]\n" + "x" * 8000 + "\n\n[TÀI LIỆU 2: small.md]\nsmall summary"
    excerpt = ollama.compact_source(source, limit)
    assert len(excerpt) <= limit
    if limit:
        assert "big.pdf" in excerpt and "small summary" in excerpt


def test_missing_model_rejected_before_chat(ollama_server):
    requests = ollama_server(tags={"models": []})
    with pytest.raises(ollama.OllamaError, match="chưa có") as exc:
        ollama.generate_lesson("Harris", "Corners", "", "qwen2.5:3b", 3)
    assert exc.value.status_code == 400
    assert len(requests) == 1


def test_default_latest_tag(ollama_server):
    ollama_server()
    assert ollama.require_model(" mistral ") == "mistral:latest"


@pytest.mark.parametrize("chat, message", [
    (httpx.ReadTimeout("slow"), "qwen2.5:3b, 3 slide"),
    (httpx.ConnectError("offline"), "Không kết nối"),
    ({"done_reason": "length"}, "hết 1600 token"),
    ({"message": {"content": ""}}, "trống"),
    ({"message": None}, "trống"),
    ({"message": {"content": "not json"}}, "không phải JSON"),
    ({"message": {"content": "{}"}}, "thiếu trường"),
    ({"error": "model unavailable"}, "model unavailable"),
])
def test_ollama_failures_are_actionable(ollama_server, chat, message):
    ollama_server(chat=chat)
    with pytest.raises(ollama.OllamaError, match=message):
        ollama.generate_lesson("Harris", "Corners", "", "qwen2.5:3b", 3)


def test_incomplete_lesson_rejected(ollama_server):
    ollama_server()
    with pytest.raises(ollama.OllamaError, match="cần đúng 4 slide"):
        ollama.generate_lesson("Harris", "Corners", "", "qwen2.5:3b", 4)


def test_model_listing_offline(monkeypatch):
    original_client = httpx.Client
    def offline(request):
        raise httpx.ConnectError("offline")
    monkeypatch.setattr(ollama.httpx, "Client", lambda **kwargs: original_client(
        transport=httpx.MockTransport(offline), **kwargs,
    ))
    with pytest.raises(ollama.OllamaError) as exc:
        ollama.require_model("qwen2.5:3b")
    assert exc.value.status_code == 503


def test_embedding_model_rejected(ollama_server):
    ollama_server(info={"capabilities": ["embedding"]})
    with pytest.raises(ollama.OllamaError, match="không hỗ trợ tạo văn bản"):
        ollama.inspect_model("qwen2.5:3b")


@pytest.mark.parametrize("thinking, expected", [({"values": [True, False]}, False), ({"values": [True]}, False),
                                                ({"values": ["low", "high"]}, "low"), (None, False)])
def test_thinking_control_respects_capabilities(ollama_server, thinking, expected):
    requests = ollama_server(info={"capabilities": ["completion", "thinking"], "thinking": thinking})
    ollama.generate_structured("qwen2.5:3b", {"type": "object"}, "Example")
    payload = json.loads(requests[-1].content)
    assert payload["think"] == expected
    assert payload["options"]["num_ctx"] == 4096


def test_regular_model_does_not_receive_thinking_flag(ollama_server):
    requests = ollama_server()
    ollama.generate_structured("qwen2.5:3b", {"type": "object"}, "Example")
    assert "think" not in json.loads(requests[-1].content)


def test_cloud_model_rejected(ollama_server):
    requests = ollama_server(tags={"models": [{"name": "large:cloud"}]})
    with pytest.raises(ollama.OllamaError, match="không sử dụng model cloud"):
        ollama.inspect_model("large:cloud")
    assert len(requests) == 1
