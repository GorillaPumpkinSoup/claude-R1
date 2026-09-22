"""개인 자산관리 대시보드 (Streamlit). scripts/run_once.py 또는 assetmgr.scheduler로
쌓인 스냅샷을 DB에서 읽어 보여주기만 한다 - 이 페이지 자체는 시세를 조회하지 않는다."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timezone  # noqa: E402

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from assetmgr import config, db  # noqa: E402
from assetmgr.signals import SIGNAL_NEUTRAL, SIGNAL_STRONG, SIGNAL_WEAK  # noqa: E402

# --- 팔레트 (dataviz 스킬의 검증된 기본 팔레트에서 가져온 값) ---
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
SURFACE = "#fcfcfb"

CLASS_ORDER = ["stock", "crypto", "cash"]  # 고정 순서 - 데이터 값 기준으로 재배열하지 않음
CLASS_COLOR = {"stock": "#2a78d6", "crypto": "#eb6834", "cash": "#1baf7a"}  # 팔레트 slot 1/2/3
CLASS_LABEL = {"stock": "주식", "crypto": "코인", "cash": "현금"}

STATUS_COLOR = {SIGNAL_STRONG: "#0ca30c", SIGNAL_NEUTRAL: INK_MUTED, SIGNAL_WEAK: "#d03b3b"}
STATUS_ICON = {SIGNAL_STRONG: "▲", SIGNAL_NEUTRAL: "●", SIGNAL_WEAK: "▼"}

st.set_page_config(page_title="자산관리 대시보드", page_icon="\U0001F4CA", layout="wide")


def status_badge(label: str) -> str:
    color = STATUS_COLOR.get(label, INK_MUTED)
    icon = STATUS_ICON.get(label, "●")
    return f'<span style="color:{color}; font-weight:600;">{icon} {label}</span>'


def fmt_money(v: float) -> str:
    return f"{v:,.0f}"


def pnl_badge(pnl: float, pnl_pct: float) -> str:
    color = "#0ca30c" if pnl >= 0 else "#d03b3b"
    icon = "▲" if pnl >= 0 else "▼"
    return f'<span style="color:{color}; font-weight:600;">{icon} {fmt_money(pnl)} ({pnl_pct * 100:+.1f}%)</span>'


@st.cache_data(ttl=60)
def load_data(db_path: str):
    conn = db.get_connection(db_path)
    try:
        latest = db.load_latest_snapshot(conn)
        history = db.load_history(conn, limit=500)
    finally:
        conn.close()
    return latest, history


latest, history = load_data(config.DB_PATH)

st.title("\U0001F4CA 자산관리 대시보드")

if not latest:
    st.warning(
        "아직 저장된 스냅샷이 없습니다. 먼저 아래 명령으로 스냅샷을 1회 생성하세요.\n\n"
        "```\npython scripts/run_once.py\n```\n\n"
        "매시간 자동 갱신을 원하면 `python -m assetmgr.scheduler`를 백그라운드로 실행하세요."
    )
    st.stop()

generated_at = datetime.fromisoformat(latest["generated_at"]).astimezone()
age_minutes = (datetime.now(timezone.utc) - datetime.fromisoformat(latest["generated_at"])).total_seconds() / 60

# --- 상단 요약: 총자산 / 총손익 / 마지막 갱신 / 포트폴리오 신호 ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("총자산", f"{fmt_money(latest['total_value'])}")
with col2:
    if latest.get("total_pnl") is not None:
        st.markdown(f"**평가손익 (매입가 대비)**  \n{pnl_badge(latest['total_pnl'], latest['total_pnl_pct'])}", unsafe_allow_html=True)
    else:
        st.markdown("**평가손익**  \n-")
with col3:
    st.markdown(f"**마지막 갱신**  \n{generated_at:%Y-%m-%d %H:%M} ({age_minutes:.0f}분 전)")
with col4:
    st.markdown(f"**포트폴리오 신호**  \n{status_badge(latest['portfolio_label'])}", unsafe_allow_html=True)

if age_minutes > config.REFRESH_INTERVAL_MINUTES * 2:
    st.info(
        f"스냅샷이 {age_minutes:.0f}분 전 데이터입니다. 스케줄러가 실행 중인지 확인하세요 "
        "(`python -m assetmgr.scheduler`)."
    )

st.divider()

# --- 배분 도넛 + 총자산 추이 ---
chart_col1, chart_col2 = st.columns([1, 2])

with chart_col1:
    st.subheader("자산군 배분")
    present_classes = [c for c in CLASS_ORDER if c in latest["allocation_value"]]
    values = [latest["allocation_value"][c] for c in present_classes]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[CLASS_LABEL[c] for c in present_classes],
                values=values,
                hole=0.55,
                marker=dict(colors=[CLASS_COLOR[c] for c in present_classes]),
                textinfo="label+percent",
                textfont=dict(color=INK_PRIMARY),
                hovertemplate="%{label}: %{value:,.0f} (%{percent})<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        showlegend=True,
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        margin=dict(t=10, b=10, l=10, r=10),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("총자산 추이")
    if len(history) > 1:
        df_hist = pd.DataFrame(
            {
                "time": [datetime.fromisoformat(h["generated_at"]).astimezone() for h in history],
                "total_value": [h["total_value"] for h in history],
            }
        )
        fig2 = go.Figure(
            data=[
                go.Scatter(
                    x=df_hist["time"],
                    y=df_hist["total_value"],
                    mode="lines",
                    line=dict(color=CLASS_COLOR["stock"], width=2),
                    hovertemplate="%{x|%m-%d %H:%M}<br>%{y:,.0f}<extra></extra>",
                )
            ]
        )
        fig2.update_layout(
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
            xaxis=dict(showgrid=False, color=INK_MUTED),
            yaxis=dict(showgrid=True, gridcolor=GRIDLINE, color=INK_MUTED),
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.caption("스냅샷이 2개 이상 쌓이면 추이 그래프가 표시됩니다.")

st.divider()

# --- 자산별 상세 테이블 ---
st.subheader("자산별 상세")
rows = []
for a in latest["assets"]:
    if a.get("error"):
        rows.append({
            "계좌": a.get("account") or "-",
            "구분": CLASS_LABEL.get(a["class"], a["class"]),
            "종목": a["label"],
            "상태": f"오류: {a['error']}",
        })
        continue
    ind = a["indicators"]
    is_cash = a["class"] == "cash"
    rows.append({
        "계좌": a.get("account") or "-",
        "구분": CLASS_LABEL.get(a["class"], a["class"]),
        "종목": a["label"],
        "수량": "-" if is_cash else a["quantity"],
        "매입가": fmt_money(a["avg_price"]) if a.get("avg_price") is not None else "-",
        "현재가": "-" if is_cash else fmt_money(a["price"]),
        "평가금액": fmt_money(a["value"]),
        "손익": f"{fmt_money(a['pnl'])} ({a['pnl_pct'] * 100:+.1f}%)" if a.get("pnl") is not None else "-",
        "1일 변동": f"{ind['change_1d_pct'] * 100:+.2f}%" if ind.get("change_1d_pct") is not None else "-",
        "RSI(14)": f"{ind['rsi14']:.0f}" if ind.get("rsi14") is not None else "-",
        "신호": "-" if is_cash else a["signal"]["label"],
        "근거": ", ".join(a["signal"]["reasons"]) or "-",
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()

# --- LLM 시장 해설 ---
st.subheader("시장 해설 (참고용)")
if latest.get("commentary"):
    st.write(latest["commentary"])
    st.caption("⚠️ 이 코멘트는 투자 자문이 아니며, 규칙 기반 지표를 참고용으로 설명한 것입니다.")
else:
    st.caption(latest.get("commentary_error") or "LLM 해설이 아직 생성되지 않았습니다.")
