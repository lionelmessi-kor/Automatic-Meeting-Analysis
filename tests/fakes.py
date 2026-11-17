"""OpenAI 클라이언트를 흉내 내는 테스트용 가짜 객체."""

from __future__ import annotations

import json
from types import SimpleNamespace

SAMPLE_ANALYSIS = {
    "summary": [
        "주간 운동 리포트 기능의 범위와 출시 일정을 논의했다.",
        "리포트 화면은 디자인 B안으로 확정했다.",
        "출시일은 12월 15일로 정했다.",
    ],
    "decisions": ["주간 리포트는 디자인 B안(카드 4장)으로 확정", "출시일 2026-12-15"],
    "action_items": [
        {"owner": "이서연", "task": "주간 집계 배치 및 리포트 API 개발", "due_date": "2026-11-28"},
        {"owner": "정하늘", "task": "QA 테스트 케이스 작성", "due_date": ""},
        {"owner": None, "task": "공유용 이미지 생성 방식 조사", "due_date": "TBD"},
    ],
}


class FakeCompletions:
    def __init__(self, contents: list[str] | None = None, chunks: list[str] | None = None, error: Exception | None = None):
        self.contents = list(contents or [json.dumps(SAMPLE_ANALYSIS, ensure_ascii=False)])
        self.chunks = chunks or ["회의록에서 ", "확인할 수 없습니다."]
        self.error = error
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        if kwargs.get("stream"):
            return iter(
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=c))]) for c in self.chunks
            )
        content = self.contents.pop(0) if len(self.contents) > 1 else self.contents[0]
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class FakeClient:
    def __init__(self, completions: FakeCompletions):
        self.chat = SimpleNamespace(completions=completions)
