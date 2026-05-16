import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MODULE_PATH = Path(__file__).resolve().parents[1] / "utils" / "llm_inference.py"
SPEC = importlib.util.spec_from_file_location("firebench_llm_inference", MODULE_PATH)
assert SPEC is not None
llm_inference = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = llm_inference
SPEC.loader.exec_module(llm_inference)
LLMInference = llm_inference.LLMInference


class FakeChatCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="go response"))],
            usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2, total_tokens=5),
        )


class RetryableFakeChatCompletions:
    def __init__(self) -> None:
        self.call_count = 0

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.call_count += 1
        if self.call_count == 1:
            error = RuntimeError("rate limited")
            error.status_code = 429  # type: ignore[attr-defined]
            raise error
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="retry response"))],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=2, total_tokens=3),
        )


class Retryable524FakeChatCompletions:
    def __init__(self) -> None:
        self.call_count = 0

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.call_count += 1
        if self.call_count == 1:
            error = RuntimeError("origin timeout")
            error.status_code = 524  # type: ignore[attr-defined]
            error.retryable = True  # type: ignore[attr-defined]
            error.retry_after = 7  # type: ignore[attr-defined]
            raise error
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="retry 524 response"))],
            usage=SimpleNamespace(prompt_tokens=2, completion_tokens=3, total_tokens=5),
        )


class FakeOpenAIClient:
    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.chat = SimpleNamespace(completions=FakeChatCompletions())


class RetryableFakeOpenAIClient:
    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.chat = SimpleNamespace(completions=RetryableFakeChatCompletions())


class Retryable524FakeOpenAIClient:
    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.chat = SimpleNamespace(completions=Retryable524FakeChatCompletions())


def test_opencode_go_uses_documented_gateway_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    clients: list[FakeOpenAIClient] = []

    def fake_openai(api_key: str, base_url: str | None = None) -> FakeOpenAIClient:
        client = FakeOpenAIClient(api_key=api_key, base_url=base_url)
        clients.append(client)
        return client

    monkeypatch.setattr(llm_inference.openai, "OpenAI", fake_openai)

    inference = LLMInference(provider="opencode_go", model_name="deepseek-v4-flash", api_key="go-key")

    assert clients[0].api_key == "go-key"
    assert clients[0].base_url == "https://opencode.ai/zen/go/v1"
    assert inference.provider == "opencode_go"


def test_opencode_go_generate_returns_normalized_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    clients: list[FakeOpenAIClient] = []

    def fake_openai(api_key: str, base_url: str | None = None) -> FakeOpenAIClient:
        client = FakeOpenAIClient(api_key=api_key, base_url=base_url)
        clients.append(client)
        return client

    monkeypatch.setattr(llm_inference.openai, "OpenAI", fake_openai)
    inference = LLMInference(provider="opencode_go", model_name="qwen3.6-plus", api_key="go-key")

    result = inference.generate("hello world", max_tokens=64, temperature=0.2)

    assert clients[0].chat.completions.calls == [
        {
            "model": "qwen3.6-plus",
            "messages": [{"role": "user", "content": "hello world"}],
            "max_tokens": 64,
            "temperature": 0.2,
        }
    ]
    assert result == {
        "content": "go response",
        "input_tokens": 3,
        "output_tokens": 2,
        "total_tokens": 5,
        "cost_usd": 0.0,
    }


def test_opencode_go_generate_forwards_extra_completion_options(monkeypatch: pytest.MonkeyPatch) -> None:
    clients: list[FakeOpenAIClient] = []

    def fake_openai(api_key: str, base_url: str | None = None) -> FakeOpenAIClient:
        client = FakeOpenAIClient(api_key=api_key, base_url=base_url)
        clients.append(client)
        return client

    monkeypatch.setattr(llm_inference.openai, "OpenAI", fake_openai)
    inference = LLMInference(provider="opencode_go", model_name="deepseek-v4-pro", api_key="go-key")

    inference.generate("judge", response_format={"type": "json_object"})

    assert clients[0].chat.completions.calls[0]["response_format"] == {"type": "json_object"}


def test_opencode_go_rejects_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENCODE_API_KEY", raising=False)
    monkeypatch.setattr(llm_inference, "OPENCODE_API_KEY", None)

    with pytest.raises(ValueError, match="OpenCode Go requires an API key"):
        LLMInference(provider="opencode_go", model_name="deepseek-v4-pro")


def test_opencode_go_retries_rate_limit_once(monkeypatch: pytest.MonkeyPatch) -> None:
    clients: list[RetryableFakeOpenAIClient] = []

    def fake_openai(api_key: str, base_url: str | None = None) -> RetryableFakeOpenAIClient:
        client = RetryableFakeOpenAIClient(api_key=api_key, base_url=base_url)
        clients.append(client)
        return client

    monkeypatch.setattr(llm_inference.openai, "OpenAI", fake_openai)
    monkeypatch.setattr(llm_inference.time, "sleep", lambda _: None)
    inference = LLMInference(provider="opencode_go", model_name="deepseek-v4-pro", api_key="go-key")

    result = inference.generate("hello")

    assert clients[0].chat.completions.call_count == 2
    assert result["content"] == "retry response"


def test_opencode_go_retries_retryable_524_once(monkeypatch: pytest.MonkeyPatch) -> None:
    clients: list[Retryable524FakeOpenAIClient] = []
    sleep_calls: list[int | float] = []

    def fake_openai(api_key: str, base_url: str | None = None) -> Retryable524FakeOpenAIClient:
        client = Retryable524FakeOpenAIClient(api_key=api_key, base_url=base_url)
        clients.append(client)
        return client

    monkeypatch.setattr(llm_inference.openai, "OpenAI", fake_openai)
    monkeypatch.setattr(llm_inference.time, "sleep", lambda seconds: sleep_calls.append(seconds))
    inference = LLMInference(provider="opencode_go", model_name="qwen3.5-plus", api_key="go-key")

    result = inference.generate("hello")

    assert clients[0].chat.completions.call_count == 2
    assert sleep_calls == [7]
    assert result["content"] == "retry 524 response"
