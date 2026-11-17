"""앱 전체 스타일 (파스텔 테마, 라이트/다크 전환).

색은 모두 CSS 변수로 정의하고, 선택한 테마의 변수 값만 바꿔 끼운다.
Streamlit 기본 테마는 .streamlit/config.toml에서 라이트로 고정하고,
다크 모드는 이 CSS가 Streamlit 위젯의 색을 덮어써서 만든다.
"""

from __future__ import annotations

import streamlit as st

THEMES: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#FFF8FB",
        "bg-dots": "#FFE6F0",
        "sidebar": "#FFF0F6",
        "card": "#FFFFFF",
        "card-soft": "#FFF5F9",
        "border": "#F7D4E3",
        "text": "#4A3B47",
        "muted": "#9A8496",
        "primary": "#E8508C",
        "primary-hover": "#D63F7B",
        "on-primary": "#FFFFFF",
        "primary-soft": "#FFE3EF",
        "mint": "#DFF6EE",
        "mint-text": "#23795E",
        "lemon": "#FFF3C9",
        "lemon-text": "#8A6500",
        "lavender": "#ECE6FF",
        "lavender-text": "#5E48BF",
        "peach": "#FFE6D9",
        "peach-text": "#B4532A",
        "shadow": "0 6px 20px rgba(232, 80, 140, 0.10)",
        "error-bg": "#FFE4E6",
        "error-text": "#B4233C",
        "warn-bg": "#FFF3C9",
        "warn-text": "#8A6500",
        "info-bg": "#E6F0FF",
        "info-text": "#2F5BB7",
        "success-bg": "#DFF6EE",
        "success-text": "#23795E",
    },
    "dark": {
        "bg": "#1D1A2A",
        "bg-dots": "#272238",
        "sidebar": "#241F34",
        "card": "#2C2640",
        "card-soft": "#332C4A",
        "border": "#463D63",
        "text": "#F4ECF7",
        "muted": "#B7A8C8",
        "primary": "#FF8FBC",
        "primary-hover": "#FFA8CB",
        "on-primary": "#2A1C28",
        "primary-soft": "#47304A",
        "mint": "#1F3B37",
        "mint-text": "#86E3C3",
        "lemon": "#3B3422",
        "lemon-text": "#FFD86E",
        "lavender": "#342C57",
        "lavender-text": "#C1B1FF",
        "peach": "#40302C",
        "peach-text": "#FFB896",
        "shadow": "0 6px 20px rgba(0, 0, 0, 0.35)",
        "error-bg": "#4A2530",
        "error-text": "#FFB3C1",
        "warn-bg": "#3B3422",
        "warn-text": "#FFD86E",
        "info-bg": "#25304A",
        "info-text": "#A9C4FF",
        "success-bg": "#1F3B37",
        "success-text": "#86E3C3",
    },
}

FONT_IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Jua&display=swap');"

_BASE_CSS = """

/* ---------- 기본 바탕 ---------- */
.stApp {
  background-color: var(--bg);
  background-image: radial-gradient(var(--bg-dots) 1.2px, transparent 1.2px);
  background-size: 22px 22px;
  color: var(--text);
}
[data-testid="stHeader"] {
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: blur(6px);
}
[data-testid="stHeader"] * { color: var(--text); }
[data-testid="stBottom"], [data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] { background: var(--bg) !important; }
.block-container { max-width: 1080px; padding-top: 2.5rem; }

/* 글꼴: 아이콘 폰트(Material Symbols)를 덮지 않도록 텍스트 요소만 지정한다 */
.stApp p, .stApp li, .stApp label, .stApp td, .stApp th,
.stApp textarea, .stApp input, .stApp .cute-body {
  font-family: 'Gowun Dodum', 'Noto Sans KR', sans-serif;
  color: var(--text);
  line-height: 1.7;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp button p, .stApp .cute-title,
.stApp [data-baseweb="tab"] p {
  font-family: 'Jua', 'Gowun Dodum', sans-serif !important;
  font-weight: 400 !important;
  color: var(--text);
  letter-spacing: 0.01em;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }
.stApp code { background: var(--primary-soft); color: var(--primary); border-radius: 8px; padding: 0.1em 0.45em; }
.stApp hr { border-color: var(--border); }
.stApp a { color: var(--primary); }

/* ---------- 사이드바 ---------- */
[data-testid="stSidebar"] { background: var(--sidebar); border-right: 2px dashed var(--border); }
[data-testid="stSidebar"] * { color: var(--text); }
[data-testid="stSidebarCollapseButton"] *, [data-testid="stExpandSidebarButton"] * { color: var(--muted) !important; }

/* ---------- 버튼 ---------- */
.stApp button[data-testid^="stBaseButton"] {
  border-radius: 999px;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}
.stApp button[data-testid="stBaseButton-secondary"] {
  background: var(--card);
  border: 2px solid var(--border);
  color: var(--text);
}
.stApp button[data-testid="stBaseButton-secondary"]:hover {
  border-color: var(--primary);
  color: var(--primary);
  transform: translateY(-1px);
}
.stApp button[data-testid="stBaseButton-secondary"]:hover p { color: var(--primary); }
.stApp button[data-testid="stBaseButton-secondary"]:disabled { opacity: 0.5; transform: none; }
.stApp button[data-testid="stBaseButton-primary"] {
  background: var(--primary);
  border: none;
  box-shadow: 0 4px 0 var(--primary-hover);
  padding: 0.55rem 2.2rem;
}
.stApp button[data-testid="stBaseButton-primary"] p { color: var(--on-primary); font-size: 1.1rem; }
.stApp button[data-testid="stBaseButton-primary"]:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 6px 0 var(--primary-hover);
}
.stApp button[data-testid="stBaseButton-primary"]:active { transform: translateY(2px); box-shadow: 0 2px 0 var(--primary-hover); }

/* ---------- 입력 ---------- */
.stApp [data-baseweb="textarea"], .stApp [data-baseweb="base-input"], .stApp textarea {
  background: var(--card) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
  border-radius: 16px !important;
}
.stApp textarea::placeholder { color: var(--muted) !important; opacity: 1; }
[data-testid="stFileUploaderDropzone"] {
  background: var(--card-soft);
  border: 2px dashed var(--border);
  border-radius: 18px;
}
[data-testid="stFileUploaderDropzone"] * { color: var(--text); }
[data-testid="stFileUploaderFile"] * { color: var(--text) !important; }

/* 탭 */
.stApp [data-baseweb="tab-list"] { gap: 0.4rem; }
.stApp [data-baseweb="tab"] {
  background: var(--card-soft);
  border-radius: 999px 999px 0 0;
  padding: 0.4rem 1rem;
}
.stApp [data-baseweb="tab"][aria-selected="true"] { background: var(--primary-soft); }
.stApp [data-baseweb="tab"][aria-selected="true"] p { color: var(--primary); }
.stApp [data-baseweb="tab-highlight"] { background: var(--primary); }
.stApp [data-baseweb="tab-border"] { background: var(--border); }

/* 펼침 영역 */
.stApp [data-testid="stExpander"] details {
  background: var(--card);
  border: 2px solid var(--border);
  border-radius: 16px;
}
.stApp [data-testid="stExpander"] summary * { color: var(--text); }

/* 알림 */
.stApp [data-testid="stAlertContainer"] { border-radius: 16px; border: none; }
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) { background: var(--error-bg); }
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) * { color: var(--error-text); }
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) { background: var(--warn-bg); }
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) * { color: var(--warn-text); }
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) { background: var(--info-bg); }
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) * { color: var(--info-text); }
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) { background: var(--success-bg); }
.stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) * { color: var(--success-text); }

/* 채팅 */
.stApp [data-testid="stChatMessage"] {
  background: var(--card);
  border: 2px solid var(--border);
  border-radius: 20px;
  padding: 0.8rem 1rem;
}
.stApp [data-testid="stChatInput"] {
  background: var(--card) !important;
  border: 2px solid var(--border) !important;
  border-radius: 999px !important;
}
.stApp [data-testid="stChatInput"] > div { background: transparent !important; border-color: transparent !important; }
.stApp [data-testid="stChatInput"] [data-baseweb="textarea"],
.stApp [data-testid="stChatInput"] [data-baseweb="base-input"],
.stApp [data-testid="stChatInput"] textarea { background: transparent !important; border: none !important; }
.stApp [data-testid="stChatInputSubmitButton"] { color: var(--primary); }

/* 스피너 */
.stApp [data-testid="stSpinner"] * { color: var(--primary); }

/* ---------- 카드 (key로 지정한 컨테이너 + HTML 카드) ---------- */
.st-key-input_card, .st-key-chat_card, .cute-card {
  background: var(--card);
  border: 2px solid var(--border);
  border-radius: 24px;
  box-shadow: var(--shadow);
  padding: 1.4rem 1.6rem;
}
.cute-card { margin-bottom: 1.1rem; }
.cute-card-title {
  font-family: 'Jua', sans-serif;
  font-size: 1.3rem;
  margin: 0 0 0.8rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text);
}
.cute-num {
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.9rem; height: 1.9rem; border-radius: 50%;
  font-size: 1rem;
}
.tone-pink .cute-num { background: var(--primary-soft); color: var(--primary); }
.tone-mint .cute-num { background: var(--mint); color: var(--mint-text); }
.tone-lavender .cute-num { background: var(--lavender); color: var(--lavender-text); }
.tone-pink { border-top: 6px solid var(--primary); }
.tone-mint { border-top: 6px solid var(--mint-text); }
.tone-lavender { border-top: 6px solid var(--lavender-text); }

/* 헤더 */
.cute-hero { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.4rem; }
.cute-mascot {
  font-size: 3rem; line-height: 1;
  background: var(--lemon); border-radius: 50%;
  width: 4.6rem; height: 4.6rem; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--shadow);
  animation: cute-bounce 2.4s ease-in-out infinite;
}
@keyframes cute-bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
@media (prefers-reduced-motion: reduce) { .cute-mascot { animation: none; } }
.cute-hero h1 { font-size: 2.1rem; margin: 0; padding: 0; line-height: 1.25; }
.cute-hero .cute-sub { color: var(--muted); margin: 0.2rem 0 0 0; }
.cute-steps { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.9rem 0 1.3rem 0; }
.cute-step {
  font-family: 'Jua', sans-serif; font-size: 0.95rem;
  padding: 0.3rem 0.9rem; border-radius: 999px;
}
.cute-step.s1 { background: var(--primary-soft); color: var(--primary); }
.cute-step.s2 { background: var(--mint); color: var(--mint-text); }
.cute-step.s3 { background: var(--lavender); color: var(--lavender-text); }
.cute-step-arrow { color: var(--muted); align-self: center; }

/* 요약 / 결정 목록 */
.cute-list { list-style: none; padding: 0; margin: 0; }
.cute-list li {
  position: relative; padding: 0.45rem 0 0.45rem 2rem;
  border-bottom: 1.5px dashed var(--border);
}
.cute-list li:last-child { border-bottom: none; }
.cute-list li::before { position: absolute; left: 0.2rem; top: 0.45rem; }
.cute-list.summary li::before { content: "🌸"; }
.cute-list.decisions li::before {
  content: "✓"; font-family: 'Jua', sans-serif;
  width: 1.3rem; height: 1.3rem; border-radius: 50%;
  background: var(--mint); color: var(--mint-text);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem; top: 0.75rem;
}
.cute-empty { color: var(--muted); margin: 0; }

/* 통계 칩 */
.cute-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; margin: 0.4rem 0 1.1rem 0; }
.cute-stat {
  border-radius: 20px; padding: 0.8rem 0.6rem; text-align: center;
  box-shadow: var(--shadow);
}
.cute-stat .label { font-size: 0.9rem; display: block; }
.cute-stat .value { font-family: 'Jua', sans-serif; font-size: 1.8rem; line-height: 1.2; display: block; }
.cute-stat.mint { background: var(--mint); } .cute-stat.mint * { color: var(--mint-text) !important; }
.cute-stat.lavender { background: var(--lavender); } .cute-stat.lavender * { color: var(--lavender-text) !important; }
.cute-stat.peach { background: var(--peach); } .cute-stat.peach * { color: var(--peach-text) !important; }

/* 할 일 표 */
.cute-table-wrap { border-radius: 16px; overflow: hidden; border: 2px solid var(--border); }
table.cute-table { width: 100%; border-collapse: collapse; table-layout: fixed; margin: 0; }
table.cute-table th {
  background: var(--lavender); color: var(--lavender-text) !important;
  font-family: 'Jua', sans-serif; font-weight: 400; text-align: left;
  padding: 0.65rem 0.8rem; border: none;
}
table.cute-table td {
  padding: 0.6rem 0.8rem; border: none; border-top: 1.5px dashed var(--border);
  vertical-align: top; word-break: keep-all; overflow-wrap: anywhere;
  background: var(--card);
}
table.cute-table tr:nth-child(even) td { background: var(--card-soft); }
table.cute-table col.c-owner { width: 22%; }
table.cute-table col.c-due { width: 24%; }
.cute-owner {
  display: inline-block; background: var(--primary-soft); color: var(--primary) !important;
  border-radius: 999px; padding: 0.05rem 0.65rem; font-size: 0.92rem;
}
.cute-due { color: var(--text); font-variant-numeric: tabular-nums; white-space: nowrap; }
.cute-undecided {
  display: inline-block; background: var(--lemon); color: var(--lemon-text) !important;
  border: 1.5px dashed var(--lemon-text);
  border-radius: 999px; padding: 0.02rem 0.6rem; font-size: 0.88rem;
}

/* 빈 화면 안내 */
.cute-placeholder { text-align: center; padding: 2.2rem 1rem; }
.cute-placeholder .big { font-size: 3rem; display: block; }

/* 섹션 제목 */
.cute-section { font-family: 'Jua', sans-serif; font-size: 1.6rem; margin: 1.6rem 0 0.6rem 0; color: var(--text); }

/* ---------- 모바일 ---------- */
@media (max-width: 640px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 3.2rem; }
  .cute-hero h1 { font-size: 1.45rem; }
  .cute-mascot { width: 3.4rem; height: 3.4rem; font-size: 2.1rem; }
  .st-key-input_card, .st-key-chat_card, .cute-card { padding: 1rem; border-radius: 20px; }
  .cute-stats { gap: 0.5rem; }
  .cute-stat .value { font-size: 1.4rem; }
  .cute-stat .label { font-size: 0.78rem; }
  table.cute-table th, table.cute-table td { padding: 0.5rem 0.35rem; font-size: 0.82rem; }
  table.cute-table col.c-owner { width: 25%; }
  table.cute-table col.c-due { width: 31%; }
  .cute-owner, .cute-undecided { padding: 0.02rem 0.45rem; font-size: 0.8rem; }
}
"""


def inject_css(theme: str) -> None:
    """선택한 테마의 CSS 변수와 공통 스타일을 페이지에 한 번 주입한다."""
    palette = THEMES.get(theme, THEMES["light"])
    variables = "\n".join(f"  --{name}: {value};" for name, value in palette.items())
    scheme = "dark" if theme == "dark" else "light"
    # @import는 스타일시트 맨 앞에 와야 적용된다.
    css = f"{FONT_IMPORT}\n:root, .stApp {{\n{variables}\n  color-scheme: {scheme};\n}}\n{_BASE_CSS}"
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
