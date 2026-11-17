"""OpenAI 호출 (회의록 분석, 추가 질문 채팅)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx
import openai
from openai import OpenAI

from core.config import get_settings
from core.prompts import build_analysis_user_prompt, build_chat_system_prompt, ANALYSIS_SYSTEM_PROMPT

UNDECIDED = "미정"
MAX_SUMMARY_LINES = 5
_PARSE_ATTEMPTS = 2  # 최초 1회 + 재시도 1회

# 요청 한 번의 최대 대기 시간과 SDK 자동 재시도 횟수.
# 오류가 계속될 때 사용자가 기다리는 최대 시간은 약 (60초 × 2회) ≈ 2분이다.
# 정상 분석은 30,000자 회의록도 이 안에 끝난다. (샘플 1,500~2,000자 기준 10~20초)
REQUEST_TIMEOUT = httpx.Timeout(60.0, connect=10.0)
MAX_RETRIES = 1

# 사용자에게 보여줄 오류 메시지 (PRD 8장)
MSG_NO_KEY = "OpenAI API 키가 설정되지 않았습니다. `.env` 파일 또는 Streamlit Secrets를 확인해주세요."
MSG_AUTH = "API 키가 올바르지 않습니다."
MSG_RATE_LIMIT = "요청이 많아 잠시 후 다시 시도해주세요."
MSG_NETWORK = "AI 서버에 연결하지 못했습니다. 네트워크 상태를 확인한 뒤 다시 시도해주세요."
MSG_TIMEOUT = "AI 응답이 너무 오래 걸려 요청을 중단했습니다. 잠시 후 다시 시도하거나 회의록을 나눠서 분석해주세요."
MSG_PARSE = "분석 결과를 처리하지 못했습니다. 다시 시도해주세요."
MSG_MODEL = "모델 '{model}'을(를) 사용할 수 없습니다. `.env`의 OPENAI_MODEL 값을 확인해주세요."
MSG_UNKNOWN = "AI 요청 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

# AI가 "정보 없음"을 다양한 표현으로 돌려줄 때 "미정"으로 통일한다.
_EMPTY_MARKERS = {"", "미정", "없음", "미상", "알 수 없음", "n/a", "na", "none", "null", "tbd", "unknown", "-"}


class LLMError(Exception):
    """사용자에게 그대로 보여줄 수 있는 한국어 메시지를 가진 예외."""


# ---------------------------------------------------------------------------
# 클라이언트 / 오류 변환
# ---------------------------------------------------------------------------
def _get_client() -> tuple[OpenAI, str]:
    settings = get_settings()
    if not settings.has_api_key:
        raise LLMError(MSG_NO_KEY)
    client = OpenAI(api_key=settings.openai_api_key, timeout=REQUEST_TIMEOUT, max_retries=MAX_RETRIES)
    return client, settings.openai_model


def _to_llm_error(exc: Exception, model: str) -> LLMError:
    if isinstance(exc, openai.AuthenticationError):
        return LLMError(MSG_AUTH)
    if isinstance(exc, openai.RateLimitError):
        return LLMError(MSG_RATE_LIMIT)
    # APITimeoutError는 APIConnectionError의 하위 클래스이므로 먼저 검사한다.
    if isinstance(exc, openai.APITimeoutError):
        return LLMError(MSG_TIMEOUT)
    if isinstance(exc, openai.APIConnectionError):
        return LLMError(MSG_NETWORK)
    if isinstance(exc, openai.NotFoundError):
        return LLMError(MSG_MODEL.format(model=model))
    return LLMError(MSG_UNKNOWN)


# ---------------------------------------------------------------------------
# 분석
# ---------------------------------------------------------------------------
def analyze_meeting(text: str) -> dict:
    """회의록을 분석해 아래 형식의 dict를 반환한다.

    {
        "summary": ["요약 문장", ...],          # 최대 5개
        "decisions": ["결정 사항", ...],
        "action_items": [{"owner": str, "task": str, "due_date": str}, ...],
    }

    JSON 모드로 호출하고, 파싱에 실패하면 1회 재시도한다. 결과는 normalize()를 거쳐 반환한다.
    실패 시 LLMError를 던진다.
    """
    client, model = _get_client()
    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": build_analysis_user_prompt(text)},
    ]

    for _ in range(_PARSE_ATTEMPTS):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
        except openai.OpenAIError as exc:
            raise _to_llm_error(exc, model) from exc

        content = response.choices[0].message.content or ""
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return normalize(data)

    raise LLMError(MSG_PARSE)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _or_undecided(value: Any) -> str:
    text = _clean_text(value)
    return UNDECIDED if text.lower() in _EMPTY_MARKERS else text


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = value.splitlines()
    elif isinstance(value, list):
        items = value
    else:
        items = [value]
    cleaned = [_clean_text(item).lstrip("-•* ").strip() for item in items]
    return [item for item in cleaned if item]


def normalize(analysis: dict) -> dict:
    """AI 응답의 누락 키와 빈 값을 정리한다.

    - summary / decisions는 문자열 목록으로 만들고, summary는 최대 5줄로 제한한다.
    - action_items의 owner, due_date가 비어 있으면 "미정"으로 채운다. task가 빈 항목은 버린다.
    """
    if not isinstance(analysis, dict):
        analysis = {}

    action_items = []
    raw_items = analysis.get("action_items") or []
    if not isinstance(raw_items, list):
        raw_items = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        task = _clean_text(item.get("task"))
        if not task:
            continue
        action_items.append(
            {
                "owner": _or_undecided(item.get("owner")),
                "task": task,
                "due_date": _or_undecided(item.get("due_date")),
            }
        )

    return {
        "summary": _as_str_list(analysis.get("summary"))[:MAX_SUMMARY_LINES],
        "decisions": _as_str_list(analysis.get("decisions")),
        "action_items": action_items,
    }


# ---------------------------------------------------------------------------
# 채팅
# ---------------------------------------------------------------------------
def chat_stream(transcript: str, analysis: dict, messages: list[dict]) -> Iterator[str]:
    """원본 회의록과 분석 결과를 근거로 추가 질문에 답한다.

    응답 텍스트 조각을 yield 하며, st.write_stream()에 그대로 넘겨 쓴다.
    messages는 [{"role": "user" | "assistant", "content": str}, ...] 형식이다.
    실패 시 LLMError를 던진다.
    """
    client, model = _get_client()
    system = build_chat_system_prompt(transcript, json.dumps(analysis, ensure_ascii=False, indent=2))
    payload = [{"role": "system", "content": system}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]

    try:
        stream = client.chat.completions.create(model=model, messages=payload, stream=True)
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except openai.OpenAIError as exc:
        raise _to_llm_error(exc, model) from exc
