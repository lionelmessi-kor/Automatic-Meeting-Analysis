"""AI 회의록 요약 & 할 일 추출 - Streamlit 메인 화면."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from core import exporter, llm
from core.config import get_settings
from core.textfile import decode_text_file
from ui import components as ui
from ui.styles import inject_css

MIN_CHARS = 50
MAX_CHARS = 30_000
SAMPLES_DIR = Path(__file__).parent / "samples"
SAMPLES = {
    "🚀 신규 기능 기획 회의": "sample1_product_planning.txt",
    "📣 마케팅팀 주간 회의": "sample2_marketing_weekly.txt",
    "📸 동아리 행사 준비 회의": "sample3_club_event.txt",
}


# ---------------------------------------------------------------------------
# 상태 / 입력 처리
# ---------------------------------------------------------------------------
def init_state() -> None:
    defaults = {
        "theme": "light",       # "light" | "dark"
        "paste_text": "",       # 텍스트 붙여넣기 입력값 (text_area key)
        "uploader_key": 0,      # 바꾸면 file_uploader가 초기화된다
        "sample_loaded": None,  # 마지막으로 불러온 샘플 이름
        "analysis": None,       # 정규화된 분석 결과 dict
        "transcript": "",       # 분석에 사용한 원본 회의록
        "analyzed_at": None,    # 분석 시각 (다운로드 파일명에 사용)
        "messages": [],         # 추가 질문 채팅 기록
        "pending_question": None,  # 예시 질문 버튼으로 보낸 질문
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)



def load_sample() -> None:
    """사이드바 [불러오기] 콜백: 샘플을 붙여넣기 입력창에 채운다."""
    name = st.session_state["sample_choice"]
    path = SAMPLES_DIR / SAMPLES[name]
    st.session_state["paste_text"] = path.read_text(encoding="utf-8")
    st.session_state["sample_loaded"] = name
    # 업로드된 파일이 있으면 그 파일이 우선 적용되므로, 샘플을 쓰려면 업로더를 비운다.
    st.session_state["uploader_key"] += 1


def toggle_theme() -> None:
    st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"


def reset_all() -> None:
    """입력, 분석 결과, 채팅을 모두 비운다. 테마 설정은 유지한다."""
    st.session_state.update(
        paste_text="", sample_loaded=None, analysis=None, transcript="",
        analyzed_at=None, messages=[], pending_question=None,
    )
    st.session_state["uploader_key"] += 1


def clear_chat() -> None:
    st.session_state["messages"] = []


def ask(question: str) -> None:
    st.session_state["pending_question"] = question


def validate(text: str) -> str | None:
    """입력이 분석 가능한지 확인한다. 문제가 있으면 경고 메시지를 반환한다."""
    length = len(text.strip())
    if length == 0:
        return "회의록 파일을 업로드하거나 텍스트를 입력해주세요."
    if length < MIN_CHARS:
        return f"회의록이 너무 짧습니다. {MIN_CHARS}자 이상 입력해주세요. (현재 {length}자)"
    if length > MAX_CHARS:
        return f"회의록이 너무 깁니다. {MAX_CHARS:,}자 이하로 줄여주세요. (현재 {length:,}자)"
    return None


# ---------------------------------------------------------------------------
# 화면
# ---------------------------------------------------------------------------
def render_header() -> None:
    left, right = st.columns([5, 1.3], vertical_alignment="center")
    with left:
        ui.hero()
    with right:
        is_dark = st.session_state["theme"] == "dark"
        st.button(
            "☀️ 라이트 모드" if is_dark else "🌙 다크 모드",
            key="theme_toggle",
            on_click=toggle_theme,
            help="화면 테마를 바꿉니다.",
            width="stretch",
        )


def render_sidebar(model: str) -> None:
    with st.sidebar:
        st.subheader("📂 샘플 회의록")
        st.radio("샘플 선택", list(SAMPLES), key="sample_choice", label_visibility="collapsed")
        st.button("불러오기", on_click=load_sample, width="stretch")
        if st.session_state["sample_loaded"]:
            st.caption(f"'{st.session_state['sample_loaded']}'을(를) 텍스트 붙여넣기 탭에 넣었어요.")

        st.divider()
        st.subheader("💡 사용 방법")
        st.markdown(
            "1. 회의록 `.txt` 파일을 올리거나 텍스트를 붙여넣어요.\n"
            "2. **분석하기** 버튼을 눌러요.\n"
            "3. 요약·결정 사항·할 일을 확인하고, 궁금한 건 질문하거나 파일로 받아요."
        )
        st.caption("파일을 올리면 붙여넣은 텍스트보다 파일이 먼저 쓰여요.")

        st.divider()
        st.button("🧹 전체 초기화", on_click=reset_all, width="stretch", help="입력, 결과, 대화를 모두 지웁니다.")
        st.caption(f"모델: `{model}`")


def render_input() -> str:
    """입력 탭을 그리고, 분석에 사용할 회의록 텍스트를 반환한다.

    규칙: 업로드한 파일이 있으면 파일을, 없으면 붙여넣은 텍스트를 사용한다.
    """
    tab_upload, tab_paste = st.tabs(["📄 파일 업로드", "✍️ 텍스트 붙여넣기"])

    file_text: str | None = None
    with tab_upload:
        uploaded = st.file_uploader(
            "회의록 .txt 파일을 선택하세요",
            type=["txt"],
            key=f"uploader_{st.session_state['uploader_key']}",
        )
        if uploaded is not None:
            try:
                file_text = decode_text_file(uploaded.getvalue())
            except ValueError as exc:
                st.error(str(exc))
            else:
                with st.expander(f"👀 미리보기: {uploaded.name} ({len(file_text):,}자)"):
                    st.text(file_text if file_text.strip() else "(빈 파일입니다)")

    with tab_paste:
        st.text_area(
            "회의록 내용을 붙여넣으세요",
            key="paste_text",
            height=300,
            placeholder="회의 일시, 참석자, 논의 내용 등을 붙여넣어 주세요.",
        )

    if file_text is not None:
        text, source = file_text, f"📄 업로드한 파일 · {uploaded.name}"
        if st.session_state["paste_text"].strip():
            st.warning(
                "파일과 붙여넣은 텍스트가 모두 있어요. 업로드한 파일을 분석합니다. "
                "붙여넣은 텍스트를 분석하려면 파일 업로드 탭에서 파일을 지워 주세요(✕)."
            )
    else:
        text = st.session_state["paste_text"]
        source = "✍️ 붙여넣은 텍스트" if text.strip() else "아직 입력이 없어요"

    length = len(text.strip())
    over = " · ⚠️ 너무 길어요" if length > MAX_CHARS else ""
    st.caption(f"분석 대상: {source} · {length:,} / {MAX_CHARS:,}자{over}")
    return text


def run_analysis(text: str) -> None:
    """회의록을 분석하고 결과를 session_state에 저장한다. 새 분석은 이전 결과와 채팅을 초기화한다."""
    with st.spinner("🐥 회의록을 꼼꼼히 읽고 있어요... 잠시만 기다려 주세요!"):
        try:
            analysis = llm.analyze_meeting(text)
        except llm.LLMError as exc:
            st.error(str(exc))
            return
        except Exception:
            st.error(llm.MSG_UNKNOWN)
            return

    st.session_state["analysis"] = analysis
    st.session_state["transcript"] = text
    st.session_state["analyzed_at"] = datetime.now()
    st.session_state["messages"] = []
    st.session_state["pending_question"] = None


def render_results() -> None:
    analysis = st.session_state["analysis"]
    analyzed_at: datetime = st.session_state["analyzed_at"]

    ui.section_title("🎀 분석 결과")
    st.caption(f"분석 시각: {analyzed_at:%Y-%m-%d %H:%M}")
    ui.stats(analysis)
    ui.summary_card(analysis["summary"])
    ui.decisions_card(analysis["decisions"], exporter.NO_DECISIONS)
    ui.action_items_card(analysis["action_items"], exporter.NO_ACTION_ITEMS)

    stamp = f"{analyzed_at:%Y%m%d_%H%M}"
    col_md, col_csv = st.columns(2)
    col_md.download_button(
        "📥 Markdown 다운로드",
        data=exporter.to_markdown(analysis, analyzed_at).encode("utf-8"),
        file_name=f"meeting_summary_{stamp}.md",
        mime="text/markdown",
        width="stretch",
    )
    col_csv.download_button(
        "📊 CSV 다운로드 (할 일)",
        data=exporter.to_csv(analysis),
        file_name=f"action_items_{stamp}.csv",
        mime="text/csv",
        width="stretch",
    )


def example_questions(analysis: dict) -> list[str]:
    owner = next(
        (
            i["owner"]
            for i in analysis["action_items"]
            if i["owner"] not in (ui.UNDECIDED, "전원") and "," not in i["owner"]
        ),
        None,
    )
    first = f"{owner} 님이 맡은 일만 정리해줘" if owner else "담당자별로 할 일을 정리해줘"
    return [
        first,
        "마감일이 가장 급한 할 일은 뭐야?",
        "결론이 나지 않은 안건은?",
        "참석자에게 보낼 공유 메일 초안 써줘",
    ]


def render_chat() -> None:
    ui.section_title("💬 궁금한 점을 물어보세요")
    with st.container(key="chat_card"):
        cols = st.columns(2)
        for idx, question in enumerate(example_questions(st.session_state["analysis"])):
            cols[idx % 2].button(question, key=f"example_q_{idx}", on_click=ask, args=(question,), width="stretch")

        # 화면 순서: 대화 기록 → 입력창 → 초기화 버튼.
        # 입력값을 먼저 읽어야 새 질문을 기록 영역에 그릴 수 있으므로, 영역을 먼저 만들어 두고 나중에 채운다.
        history_area = st.container()
        input_area = st.container()
        footer_area = st.container()

        with input_area:
            typed = st.chat_input("분석 결과에 대해 질문해 보세요")
        question = typed or st.session_state.pop("pending_question", None)
        st.session_state["pending_question"] = None

        with history_area:
            for message in st.session_state["messages"]:
                avatar = "🐥" if message["role"] == "assistant" else "🙋"
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])

            if question:
                messages = st.session_state["messages"]
                messages.append({"role": "user", "content": question})
                with st.chat_message("user", avatar="🙋"):
                    st.markdown(question)
                with st.chat_message("assistant", avatar="🐥"):
                    try:
                        answer = st.write_stream(
                            llm.chat_stream(st.session_state["transcript"], st.session_state["analysis"], messages)
                        )
                    except Exception as exc:
                        messages.pop()  # 실패한 질문은 기록에서 빼서 다음 요청에 남지 않게 한다
                        st.error(str(exc) if isinstance(exc, llm.LLMError) else llm.MSG_UNKNOWN)
                    else:
                        messages.append(
                            {"role": "assistant", "content": answer if isinstance(answer, str) else str(answer)}
                        )

        if st.session_state["messages"]:
            with footer_area:
                st.button("🧽 대화 초기화", key="clear_chat", on_click=clear_chat)


def main() -> None:
    st.set_page_config(page_title="AI 회의록 요약", page_icon="🐥", layout="wide")
    init_state()
    inject_css(st.session_state["theme"])
    settings = get_settings()

    render_sidebar(settings.openai_model)
    render_header()

    with st.container(key="input_card"):
        text = render_input()
        clicked = st.button("🔍 분석하기", type="primary", key="analyze")

    if clicked:
        warning = validate(text)
        if warning:
            st.warning(warning)
        else:
            run_analysis(text.strip())

    if st.session_state["analysis"] is None:
        ui.placeholder()
        return

    if text.strip() and text.strip() != st.session_state["transcript"]:
        st.info("입력한 회의록이 바뀌었어요. 새 내용으로 보려면 [분석하기]를 다시 눌러 주세요. 아래는 이전 결과예요.")
    render_results()
    render_chat()


if __name__ == "__main__":
    main()
