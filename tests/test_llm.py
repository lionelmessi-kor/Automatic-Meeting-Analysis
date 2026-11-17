import httpx
import openai
import pytest

from core import llm
from core.config import Settings
from tests.fakes import FakeClient, FakeCompletions


@pytest.fixture
def fake(monkeypatch):
    """llm._get_client가 가짜 클라이언트를 돌려주게 한다."""

    def install(**kwargs) -> FakeCompletions:
        completions = FakeCompletions(**kwargs)
        monkeypatch.setattr(llm, "_get_client", lambda: (FakeClient(completions), "gpt-6.1-sol"))
        return completions

    return install


# ---------------------------------------------------------------------------
# normalize
# ---------------------------------------------------------------------------
def test_normalize_fills_missing_owner_and_due_date():
    result = llm.normalize(
        {
            "summary": ["a"],
            "decisions": [],
            "action_items": [
                {"task": "키 없음"},
                {"owner": "", "task": "빈 문자열", "due_date": None},
                {"owner": "N/A", "task": "영문 표기", "due_date": "TBD"},
                {"owner": "김민수", "task": "정상", "due_date": "2026-11-24"},
            ],
        }
    )
    owners = [i["owner"] for i in result["action_items"]]
    dues = [i["due_date"] for i in result["action_items"]]
    assert owners == ["미정", "미정", "미정", "김민수"]
    assert dues == ["미정", "미정", "미정", "2026-11-24"]


def test_normalize_handles_missing_keys_and_bad_types():
    assert llm.normalize({}) == {"summary": [], "decisions": [], "action_items": []}
    assert llm.normalize("not a dict") == {"summary": [], "decisions": [], "action_items": []}
    result = llm.normalize({"action_items": "문자열", "decisions": None})
    assert result["action_items"] == [] and result["decisions"] == []


def test_normalize_drops_items_without_task_and_non_dicts():
    result = llm.normalize({"action_items": [{"owner": "김민수", "task": "  "}, "문자열 항목", {"task": "남는 일"}]})
    assert [i["task"] for i in result["action_items"]] == ["남는 일"]


def test_normalize_limits_summary_to_five_lines_and_splits_string():
    assert len(llm.normalize({"summary": [f"문장 {i}" for i in range(8)]})["summary"]) == 5
    assert llm.normalize({"summary": "- 첫째\n- 둘째\n\n"})["summary"] == ["첫째", "둘째"]


# ---------------------------------------------------------------------------
# analyze_meeting
# ---------------------------------------------------------------------------
def test_analyze_meeting_returns_normalized_result(fake):
    completions = fake()
    result = llm.analyze_meeting("회의록 본문")
    assert result["action_items"][1]["due_date"] == "미정"
    assert result["action_items"][2] == {"owner": "미정", "task": "공유용 이미지 생성 방식 조사", "due_date": "미정"}
    call = completions.calls[0]
    assert call["model"] == "gpt-6.1-sol"
    assert call["response_format"] == {"type": "json_object"}
    assert "회의록 본문" in call["messages"][1]["content"]


def test_analyze_meeting_retries_once_on_bad_json(fake):
    completions = fake(contents=["이건 JSON이 아님", '{"summary": ["ok"]}'])
    assert llm.analyze_meeting("x")["summary"] == ["ok"]
    assert len(completions.calls) == 2


def test_analyze_meeting_gives_up_after_retry(fake):
    completions = fake(contents=["깨진 응답"])
    with pytest.raises(llm.LLMError, match="분석 결과를 처리하지 못했습니다"):
        llm.analyze_meeting("x")
    assert len(completions.calls) == 2


def test_missing_api_key_raises_friendly_error(monkeypatch):
    monkeypatch.setattr(llm, "get_settings", lambda: Settings(openai_api_key=None, openai_model="gpt-6.1-sol"))
    with pytest.raises(llm.LLMError, match="API 키가 설정되지 않았습니다"):
        llm.analyze_meeting("x")


def test_client_limits_worst_case_wait(monkeypatch):
    """오류가 계속돼도 사용자가 기다리는 시간이 약 2분을 넘지 않아야 한다."""
    monkeypatch.setattr(llm, "get_settings", lambda: Settings(openai_api_key="sk-test", openai_model="m"))
    client, _ = llm._get_client()
    assert client.max_retries == 1
    assert client.timeout.read == 60.0 and client.timeout.connect == 10.0
    worst_case = client.timeout.read * (client.max_retries + 1)
    assert worst_case <= 120


def _api_error(cls, status: int):
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return cls("error", response=httpx.Response(status, request=request), body=None)


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (_api_error(openai.AuthenticationError, 401), llm.MSG_AUTH),
        (_api_error(openai.RateLimitError, 429), llm.MSG_RATE_LIMIT),
        (openai.APIConnectionError(request=httpx.Request("POST", "https://x")), llm.MSG_NETWORK),
        (openai.APITimeoutError(request=httpx.Request("POST", "https://x")), llm.MSG_TIMEOUT),
        (_api_error(openai.NotFoundError, 404), llm.MSG_MODEL.format(model="gpt-6.1-sol")),
    ],
)
def test_api_errors_are_converted(fake, error, message):
    fake(error=error)
    with pytest.raises(llm.LLMError) as info:
        llm.analyze_meeting("x")
    assert str(info.value) == message


# ---------------------------------------------------------------------------
# chat_stream
# ---------------------------------------------------------------------------
def test_chat_stream_yields_chunks_and_sends_context(fake):
    completions = fake(chunks=["안녕", "하세요"])
    messages = [{"role": "user", "content": "질문 {중괄호}"}]
    assert "".join(llm.chat_stream("원본 {회의록}", {"summary": ["요약"]}, messages)) == "안녕하세요"
    sent = completions.calls[0]["messages"]
    assert sent[0]["role"] == "system"
    assert "원본 {회의록}" in sent[0]["content"] and '"요약"' in sent[0]["content"]
    assert sent[1] == messages[0]
    assert completions.calls[0]["stream"] is True


def test_chat_stream_converts_errors(fake):
    fake(error=_api_error(openai.RateLimitError, 429))
    with pytest.raises(llm.LLMError, match="잠시 후"):
        list(llm.chat_stream("t", {}, [{"role": "user", "content": "q"}]))
