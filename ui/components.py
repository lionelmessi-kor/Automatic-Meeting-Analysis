"""결과 카드, 표 등 HTML로 그리는 화면 조각.

회의록과 AI 응답에서 온 텍스트는 모두 html.escape를 거친 뒤 HTML에 넣는다.
st.markdown은 줄 앞 공백을 코드 블록으로 해석하므로 HTML은 한 줄로 이어 붙인다.
"""

from __future__ import annotations

from html import escape

import streamlit as st

UNDECIDED = "미정"


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def hero() -> None:
    _html(
        '<div class="cute-hero">'
        '<div class="cute-mascot" aria-hidden="true">🐥</div>'
        "<div>"
        '<h1 class="cute-title">AI 회의록 요약 &amp; 할 일 추출</h1>'
        '<p class="cute-sub">회의록만 주시면 요약, 결정 사항, 할 일을 쏙쏙 정리해 드릴게요!</p>'
        "</div></div>"
        '<div class="cute-steps">'
        '<span class="cute-step s1">① 회의록 넣기</span><span class="cute-step-arrow">›</span>'
        '<span class="cute-step s2">② 분석하기</span><span class="cute-step-arrow">›</span>'
        '<span class="cute-step s3">③ 확인하고 질문하기</span>'
        "</div>"
    )


def section_title(text: str) -> None:
    _html(f'<div class="cute-section">{escape(text)}</div>')


def placeholder() -> None:
    _html(
        '<div class="cute-card cute-placeholder">'
        '<span class="big" aria-hidden="true">🐣</span>'
        '<p class="cute-body">아직 분석 결과가 없어요.<br>회의록을 넣고 <b>분석하기</b>를 눌러 주세요!</p>'
        "</div>"
    )


def stats(analysis: dict) -> None:
    items = analysis["action_items"]
    undecided = sum(1 for i in items for key in ("owner", "due_date") if i[key] == UNDECIDED)
    _html(
        '<div class="cute-stats">'
        f'<div class="cute-stat mint"><span class="label">✅ 결정 사항</span><span class="value">{len(analysis["decisions"])}</span></div>'
        f'<div class="cute-stat lavender"><span class="label">📝 할 일</span><span class="value">{len(items)}</span></div>'
        f'<div class="cute-stat peach"><span class="label">🤔 미정 항목</span><span class="value">{undecided}</span></div>'
        "</div>"
    )


def _card(tone: str, number: str, title: str, body: str) -> None:
    _html(
        f'<div class="cute-card tone-{tone}">'
        f'<div class="cute-card-title"><span class="cute-num">{number}</span>{escape(title)}</div>'
        f"{body}</div>"
    )


def _list(items: list[str], kind: str, empty: str) -> str:
    if not items:
        return f'<p class="cute-empty">{escape(empty)}</p>'
    lis = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f'<ul class="cute-list {kind}">{lis}</ul>'


def summary_card(summary: list[str]) -> None:
    _card("pink", "1", "회의 핵심 요약", _list(summary, "summary", "요약을 만들지 못했어요."))


def decisions_card(decisions: list[str], empty: str) -> None:
    _card("mint", "2", "주요 결정 사항", _list(decisions, "decisions", empty))


def _cell(value: str, kind: str) -> str:
    if value == UNDECIDED:
        return f'<span class="cute-undecided">{UNDECIDED}</span>'
    if kind == "owner":
        return f'<span class="cute-owner">{escape(value)}</span>'
    if kind == "due":
        return f'<span class="cute-due">{escape(value)}</span>'
    return escape(value)


def action_items_card(action_items: list[dict], empty: str) -> None:
    if not action_items:
        _card("lavender", "3", "할 일 (Action Items)", f'<p class="cute-empty">{escape(empty)}</p>')
        return
    rows = "".join(
        "<tr>"
        f'<td>{_cell(i["owner"], "owner")}</td>'
        f'<td>{_cell(i["task"], "task")}</td>'
        f'<td>{_cell(i["due_date"], "due")}</td>'
        "</tr>"
        for i in action_items
    )
    table = (
        '<div class="cute-table-wrap"><table class="cute-table">'
        '<colgroup><col class="c-owner"><col><col class="c-due"></colgroup>'
        "<thead><tr><th>담당자</th><th>할 일</th><th>마감일</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )
    _card("lavender", "3", "할 일 (Action Items)", table)
