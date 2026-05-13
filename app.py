"""News Clipper — Streamlit web UI.

Run: streamlit run app.py
Multi-query news search with Toss-inspired clean design.
"""

from __future__ import annotations

import io
import re
from datetime import datetime

import streamlit as st

from core import (
    COLUMNS_MULTI,
    dedupe_multi,
    fetch_for_queries,
    filter_trusted,
    rows_for_multi,
    write_xlsx_multi,
)

MAX_QUERIES = 7

# ---------------------------------------------------------------------------
# Page config + Toss-inspired CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="News Clipper",
    page_icon="🗞️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

_TOSS_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.min.css');

html, body, [class*="css"], .stApp, .stMarkdown, .stTextInput, .stTextArea,
.stNumberInput, .stButton, .stDataFrame, .stDownloadButton {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui,
                 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
}

/* Hide Streamlit chrome */
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

/* Centered narrow layout */
.block-container {
    max-width: 720px !important;
    padding-top: 2.5rem !important;
    padding-bottom: 4rem !important;
}

/* Title block */
.nc-title {
    font-size: 30px;
    font-weight: 800;
    color: #191F28;
    margin-bottom: 4px;
    letter-spacing: -0.4px;
}
.nc-caption {
    font-size: 14px;
    color: #8B95A1;
    margin-bottom: 28px;
}

/* Cards (uses st.container(border=True) → wraps in this testid) */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #E5E8EB !important;
    border-radius: 14px !important;
    padding: 20px 22px !important;
    box-shadow: none !important;
}

/* Labels */
.stTextInput label, .stTextArea label, .stNumberInput label {
    font-weight: 600 !important;
    color: #191F28 !important;
    font-size: 14px !important;
}

/* Inputs (text + number + textarea) */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background-color: #F9FAFB !important;
    border: 1px solid #E5E8EB !important;
    border-radius: 12px !important;
    padding: 12px 14px !important;
    font-size: 16px !important;
    color: #191F28 !important;
    transition: border-color 0.15s ease;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #3182F6 !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(49, 130, 246, 0.15) !important;
}

/* Number input chevrons */
.stNumberInput button {
    background-color: #F2F4F6 !important;
    border-color: #E5E8EB !important;
    color: #4E5968 !important;
}

/* Primary button */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    background: #3182F6 !important;
    color: #FFFFFF !important;
    border: 0 !important;
    border-radius: 14px !important;
    padding: 14px 0 !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    width: 100% !important;
    box-shadow: none !important;
    transition: background-color 0.15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #1B64DA !important;
    color: #FFFFFF !important;
}
.stButton > button:disabled, .stFormSubmitButton > button:disabled {
    background: #D1D6DB !important;
    color: #FFFFFF !important;
    cursor: not-allowed !important;
}

/* DataFrame styling */
[data-testid="stDataFrame"] {
    border: 1px solid #E5E8EB;
    border-radius: 12px;
    overflow: hidden;
}

/* Alerts (success / warning / error) — softer Toss-tone palette */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: 0 !important;
    padding: 14px 16px !important;
    font-size: 14px !important;
}

/* st.status header */
[data-testid="stStatusContainer"], details[data-testid="stExpander"] {
    border: 1px solid #E5E8EB !important;
    border-radius: 12px !important;
    background: #F9FAFB !important;
}

/* Section spacing */
.nc-spacer { height: 24px; }
</style>
"""

st.markdown(_TOSS_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_INVALID_FNAME_CHARS = re.compile(r'[\\/:*?"<>|\r\n\t]')


def sanitize_filename(name: str) -> str:
    name = (name or "").strip()
    if not name:
        name = f"News Clipping_{datetime.now().strftime('%y%m%d')}"
    name = _INVALID_FNAME_CHARS.sub("_", name)
    if not name.lower().endswith(".xlsx"):
        name = f"{name}.xlsx"
    return name


def default_filename() -> str:
    return f"News Clipping_{datetime.now().strftime('%y%m%d')}.xlsx"


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="nc-title">🗞️ News Clipper</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="nc-caption">키워드 기반 뉴스 수집 → xlsx 정리. 최대 7개 쿼리 동시 검색.</div>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Input card (form)
# ---------------------------------------------------------------------------
with st.container(border=True):
    with st.form("search_form", clear_on_submit=False):
        queries_text = st.text_area(
            f"검색어 (한 줄에 1쿼리, 최대 {MAX_QUERIES}줄)",
            placeholder=(
                '예)\n'
                'M&A OR 인수 OR 합병\n'
                '"적대적 인수"\n'
                'site:reuters.com merger'
            ),
            height=180,
            key="queries_text",
        )

        col1, col2 = st.columns([1, 2])
        with col1:
            days = st.number_input(
                "지난 N일", min_value=1, max_value=90, value=1, step=1, key="days"
            )
        with col2:
            filename = st.text_input(
                "파일명",
                value=default_filename(),
                key="filename",
                help="비워두면 자동으로 'News Clipping_yymmdd.xlsx'로 저장됩니다.",
            )

        trusted_text = st.text_area(
            "신뢰 언론사 (선택, 한 줄에 하나)",
            placeholder="한국경제\n매일경제\nReuters\nBloomberg",
            height=120,
            key="trusted_text",
        )

        submitted = st.form_submit_button("🔍 검색", use_container_width=True)


# ---------------------------------------------------------------------------
# Search & results
# ---------------------------------------------------------------------------
if submitted:
    raw_queries = [q.strip() for q in (queries_text or "").splitlines()]
    queries = [q for q in raw_queries if q]

    if not queries:
        st.error("최소 1개의 검색어를 입력하세요.")
        st.stop()
    if len(queries) > MAX_QUERIES:
        st.error(f"최대 {MAX_QUERIES}줄까지 입력 가능합니다 (현재 {len(queries)}줄).")
        st.stop()

    whitelist = [w.strip() for w in (trusted_text or "").splitlines() if w.strip()]

    with st.status(
        f"{len(queries)}개 쿼리 병렬 검색 중...", expanded=False
    ) as status:
        items = fetch_for_queries(queries, days=int(days))
        status.update(label=f"수집: {len(items)}건. 중복 제거 중...")
        items = dedupe_multi(items)
        if whitelist:
            items = filter_trusted(items, whitelist)
            status.update(
                label=f"필터 적용 후: {len(items)}건. 파일 생성 중..."
            )
        else:
            status.update(label=f"중복 제거 후: {len(items)}건. 파일 생성 중...")
        status.update(label="완료", state="complete")

    st.markdown('<div class="nc-spacer"></div>', unsafe_allow_html=True)

    with st.container(border=True):
        if not items:
            st.warning("결과가 없습니다. 검색어 / 기간 / 언론사 필터를 조정해 보세요.")
        else:
            st.markdown(
                f'<div style="font-size:18px;font-weight:700;color:#191F28;margin-bottom:12px;">'
                f"✅ {len(items)}건 수집 완료"
                f"</div>",
                unsafe_allow_html=True,
            )

            preview_rows = rows_for_multi(items)
            data = {col: [r[i] for r in preview_rows] for i, col in enumerate(COLUMNS_MULTI)}

            st.dataframe(
                data,
                use_container_width=True,
                height=420,
                hide_index=True,
                column_config={
                    "검색 쿼리": st.column_config.TextColumn("검색 쿼리", width="medium"),
                    "매칭 키워드": st.column_config.TextColumn("매칭 키워드", width="small"),
                    "제목": st.column_config.TextColumn("제목", width="large"),
                    "링크": st.column_config.LinkColumn(
                        "링크", display_text="🔗 열기", width="small"
                    ),
                    "언론사": st.column_config.TextColumn("언론사", width="small"),
                    "발행일시": st.column_config.TextColumn("발행일시", width="medium"),
                },
            )

            buf = io.BytesIO()
            write_xlsx_multi(items, buf)
            buf.seek(0)
            out_name = sanitize_filename(filename)
            st.download_button(
                label=f"📥 {out_name} 다운로드",
                data=buf.getvalue(),
                file_name=out_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
