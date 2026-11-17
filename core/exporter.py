"""분석 결과를 표 / Markdown / CSV로 변환한다."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

COLUMNS = {"owner": "담당자", "task": "할 일", "due_date": "마감일"}
NO_DECISIONS = "확정된 결정 사항이 없습니다."
NO_ACTION_ITEMS = "추출된 할 일이 없습니다."


def to_dataframe(analysis: dict) -> pd.DataFrame:
    """할 일 목록을 '담당자 / 할 일 / 마감일' 열의 DataFrame으로 만든다."""
    rows = [{label: item.get(key, "") for key, label in COLUMNS.items()} for item in analysis.get("action_items", [])]
    return pd.DataFrame(rows, columns=list(COLUMNS.values()))


def _md_cell(value: str) -> str:
    """Markdown 표 셀에서 표를 깨뜨리는 문자를 처리한다."""
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def to_markdown(analysis: dict, generated_at: datetime | None = None) -> str:
    """요약, 결정 사항, 할 일 표를 담은 Markdown 문자열을 만든다."""
    generated_at = generated_at or datetime.now()
    lines = [
        "# 회의 분석 결과",
        f"> 생성 일시: {generated_at:%Y-%m-%d %H:%M}",
        "",
        "## 1. 회의 핵심 요약",
    ]
    lines += [f"- {s}" for s in analysis.get("summary", [])] or ["- (요약 없음)"]

    lines += ["", "## 2. 주요 결정 사항"]
    lines += [f"- {d}" for d in analysis.get("decisions", [])] or [f"- {NO_DECISIONS}"]

    lines += ["", "## 3. 할 일 (Action Items)"]
    items = analysis.get("action_items", [])
    if items:
        lines += ["| 담당자 | 할 일 | 마감일 |", "|---|---|---|"]
        lines += [
            f"| {_md_cell(i.get('owner', ''))} | {_md_cell(i.get('task', ''))} | {_md_cell(i.get('due_date', ''))} |"
            for i in items
        ]
    else:
        lines.append(f"- {NO_ACTION_ITEMS}")

    return "\n".join(lines) + "\n"


_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: str) -> str:
    """Excel이 수식으로 실행하지 않도록 수식 시작 문자 앞에 '를 붙인다 (CSV 수식 주입 방지).

    회의록 내용이 AI 응답을 거쳐 그대로 셀에 들어가므로, "=HYPERLINK(...)" 같은 값이 실행될 수 있다.
    """
    text = str(value)
    return f"'{text}" if text.startswith(_FORMULA_PREFIXES) else text


def to_csv(analysis: dict) -> bytes:
    """할 일 표를 CSV 바이트로 만든다. Excel에서 한글이 깨지지 않도록 utf-8-sig(BOM)로 인코딩한다."""
    df = to_dataframe(analysis).map(_csv_safe)
    return df.to_csv(index=False, lineterminator="\r\n").encode("utf-8-sig")
