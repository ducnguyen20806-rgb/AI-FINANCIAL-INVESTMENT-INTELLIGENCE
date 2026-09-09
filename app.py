"""
app.py
GIAO DIỆN STREAMLIT — AI Financial & Investment Intelligence Platform
Thiết kế lại theo phong cách Glassmorphism & Financial Dark Theme:
1. Fixed Top Navigation Bar: Logo, Search Bar, Server status, User profile & Logout.
2. Left Navigation Panel: Sidebar 240px chứa danh sách chuyển đổi màn hình dạng icon + text.
3. Main Canvas Grid: Display Font cho mã cổ phiếu, Ticker Strip liền mạch, Scorecards trực quan với mini-meter.
"""
from __future__ import annotations

import datetime
from typing import Any

import pandas as pd
import requests
import streamlit as st

from common.utils import fmt_vnd, pct, safe_float
from config import app_config, finance_config
from ui.charts import (
    candlestick_chart,
    dcf_chart,
    dcf_sensitivity_heatmap,
    drawdown_chart,
    efficient_frontier_chart,
    financial_history_chart,
    momentum_chart,
    multi_ticker_radar_chart,
    scenario_chart,
    wacc_chart,
)
from ui.login import render_login_screen
from ui.theme import (
    ACTION_COLORS,
    COLORS,
    PILLAR_LABELS,
    ZONE_COLORS,
    build_css,
    price_color,
    score_color,
)

st.set_page_config(
    page_title="AI Financial & Investment Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(build_css(), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tầng dữ liệu (Data Layer)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=app_config.cache_ttl_seconds, show_spinner=False)
def analyze_direct(symbol: str, rf: float, erp: float, g: float,
                   tax: float) -> dict[str, Any]:
    """Gọi thẳng DecisionEngine trong tiến trình Streamlit."""
    finance_config.risk_free_rate = rf
    finance_config.equity_risk_premium = erp
    finance_config.terminal_growth = g
    finance_config.corporate_tax_rate = tax

    from Module6.decision_engine import DecisionEngine
    return DecisionEngine(config=finance_config).analyze(symbol)


@st.cache_data(ttl=120, show_spinner=False)
def analyze_via_api(symbol: str, base_url: str) -> dict[str, Any]:
    """Gọi API Gateway."""
    url = f"{base_url.rstrip('/')}/api/v1/analyze/{symbol}"
    resp = requests.get(url, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"API trả về {resp.status_code}: {resp.text[:200]}")
    return resp.json()


# ---------------------------------------------------------------------------
# Cổng bảo vệ xác thực (Lamp Login & Register Gateway)
# ---------------------------------------------------------------------------
if st.query_params.get("auth") == "true":
    st.session_state["authenticated"] = True
    if "username" not in st.session_state or not st.session_state["username"]:
        st.session_state["username"] = st.query_params.get("user", "Admin")

# Nếu chưa đăng nhập: chỉ hiển thị cổng Lamp Login rồi dừng lại
# Khi đã đăng nhập: loại bỏ 100% phần đăng nhập, chỉ hiển thị Dashboard chính
if not st.session_state.get("authenticated", False):
    # Pre-heat nạp sẵn dữ liệu FPT ngầm ngay trong lúc user xem màn hình login
    # Nhờ vậy, ngay khi bấm Đăng nhập, Dashboard đã có sẵn trong RAM và mở tức thì (<0.1s)!
    if not st.session_state.get("_preheat_started", False):
        st.session_state["_preheat_started"] = True
        import threading
        threading.Thread(
            target=analyze_direct,
            args=(
                "FPT",
                float(finance_config.risk_free_rate),
                float(finance_config.equity_risk_premium),
                float(finance_config.terminal_growth),
                float(finance_config.corporate_tax_rate),
            ),
            daemon=True,
        ).start()

    render_login_screen()
    st.stop()

if st.session_state.pop("is_new_user", False):
    st.toast(f"🎉 Chào mừng {st.session_state.get('username', 'Trader')} gia nhập nền tảng định lượng!", icon="🚀")


# ---------------------------------------------------------------------------
# Tên đầy đủ của các cổ phiếu phổ biến
# ---------------------------------------------------------------------------
COMPANY_NAMES: dict[str, str] = {
    "FPT": "Công ty Cổ phần FPT",
    "HPG": "Công ty Cổ phần Tập đoàn Hòa Phát",
    "VNM": "Công ty Cổ phần Sữa Việt Nam (Vinamilk)",
    "MWG": "Công ty Cổ phần Đầu tư Thế Giới Di Động",
    "VCB": "Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)",
    "SSI": "Công ty Cổ phần Chứng khoán SSI",
    "VIC": "Tập đoàn Vingroup - CTCP",
    "VHM": "Công ty Cổ phần Vinhomes",
    "TCB": "Ngân hàng TMCP Kỹ thương Việt Nam (Techcombank)",
    "MBB": "Ngân hàng TMCP Quân đội (MBBank)",
    "DGC": "Công ty Cổ phần Tập đoàn Hóa chất Đức Giang",
    "MSN": "Công ty Cổ phần Tập đoàn Masan",
    "STB": "Ngân hàng TMCP Sài Gòn Thương Tín (Sacombank)",
    "VRE": "Công ty Cổ phần Vincom Retail",
    "GAS": "Tổng Công ty Khí Việt Nam - CTCP (PV GAS)",
    "PLX": "Tập đoàn Xăng dầu Việt Nam (Petrolimex)",
    "BID": "Ngân hàng TMCP Đầu tư và Phát triển Việt Nam",
    "CTG": "Ngân hàng TMCP Công thương Việt Nam",
    "VJC": "Công ty Cổ phần Hàng không VietJet",
    "PNJ": "Công ty Cổ phần Vàng bạc Đá quý Phú Nhuận",
}


# ---------------------------------------------------------------------------
# Thành phần giao diện cao cấp (Top Bar, Ticker Strip, Scorecards)
# ---------------------------------------------------------------------------
def render_top_navbar(symbol: str, source_label: str, user_name: str) -> None:
    """Fixed Top Navigation Bar chứa Logo, Search Bar, Server status, User profile & Logout."""
    col_brand, col_search, col_src, col_user, col_logout = st.columns(
        [2.6, 2.5, 2.0, 1.8, 1.1], gap="small"
    )
    with col_brand:
        st.markdown(
            f'<div class="nav-brand">'
            f'<span class="nav-logo">⚡</span>'
            f'<div><div class="nav-title">AI QUANT INTELLIGENCE</div>'
            f'<div class="nav-subtitle">Institutional Financial Terminal · VNINDEX</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_search:
        with st.form("top_search_form", border=False):
            c_input, c_btn = st.columns([3, 1], gap="small")
            sym_val = c_input.text_input(
                "Mã CK",
                value=symbol,
                max_chars=8,
                label_visibility="collapsed",
                placeholder="Nhập mã (FPT, HPG...)",
            )
            btn_search = c_btn.form_submit_button("🔍 Tìm", use_container_width=True)
            if btn_search and sym_val:
                st.session_state.last_symbol = sym_val.upper().strip()
                st.rerun()

    with col_src:
        st.markdown(
            f'<div style="padding-top:6px;">'
            f'<span class="badge" style="background:rgba(0,197,102,0.15);color:{COLORS["up"]};border:1px solid rgba(0,197,102,0.3);font-size:11px;">'
            f'● {source_label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_user:
        st.markdown(
            f'<div style="padding-top:5px;display:flex;align-items:center;gap:6px;">'
            f'<span style="font-size:12px;font-weight:700;color:{COLORS["gold"]};">👤 {user_name}</span>'
            f'<span class="badge" style="background:rgba(216,180,95,0.15);color:{COLORS["gold"]};border:1px solid rgba(216,180,95,0.3);font-size:10px;">QUANT PRO</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_logout:
        if st.button("🚪 Thoát", use_container_width=True, help="Đăng xuất khỏi hệ thống"):
            st.session_state["authenticated"] = False
            st.session_state.pop("username", None)
            st.query_params.clear()
            st.rerun()


def render_company_header(symbol: str, quote: dict[str, Any], elapsed_ms: int, data_source: str) -> None:
    """Header Mã cổ phiếu với Display Font lớn, tên đầy đủ và trạng thái nguồn dữ liệu."""
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    company_name = COMPANY_NAMES.get(symbol, f"Công ty Cổ phần {symbol}")
    exchange = quote.get("exchange", "HOSE")

    st.markdown(
        f'<div class="company-header">'
        f'<div class="company-title-wrap">'
        f'<span class="company-symbol-display">{symbol}</span>'
        f'<div>'
        f'<div class="company-fullname">{symbol} — {company_name}</div>'
        f'<div class="company-sector">Sàn giao dịch: <b>{exchange}</b> · Cập nhật: <b>{now_str}</b> · Nguồn: <b>{data_source}</b> ({elapsed_ms} ms)</div>'
        f'</div></div>'
        f'<div>'
        f'<span class="badge" style="background:rgba(56,189,248,0.12);color:{COLORS["accent"]};border:1px solid rgba(56,189,248,0.3);">'
        f'Real-time Market Analytics'
        f'</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_ticker_strip(quote: dict[str, Any]) -> None:
    """Thanh Ticker Strip nằm ngang liền mạch, phân cách bằng border-r."""
    price = safe_float(quote.get("price"))
    ref = safe_float(quote.get("ref_price"))
    ceiling = safe_float(quote.get("ceiling"))
    floor = safe_float(quote.get("floor"))
    change = safe_float(quote.get("change"))
    change_pct = safe_float(quote.get("change_pct"))
    c_price = price_color(price, ref, ceiling, floor)
    high = safe_float(quote.get("high"))
    low = safe_float(quote.get("low"))
    volume = safe_float(quote.get("volume"))
    value = safe_float(quote.get("value"))

    html = f"""
    <div class="ticker-strip">
      <div class="ticker-cell">
        <div class="ticker-label">Giá Trần</div>
        <div class="ticker-value" style="color:{COLORS['ceiling']}">{ceiling:,.0f}</div>
        <div class="ticker-sub">+6.9%</div>
      </div>
      <div class="ticker-cell">
        <div class="ticker-label">Tham Chiếu</div>
        <div class="ticker-value" style="color:{COLORS['reference']}">{ref:,.0f}</div>
        <div class="ticker-sub">0.0%</div>
      </div>
      <div class="ticker-cell">
        <div class="ticker-label">Giá Sàn</div>
        <div class="ticker-value" style="color:{COLORS['floor']}">{floor:,.0f}</div>
        <div class="ticker-sub">-6.9%</div>
      </div>
      <div class="ticker-cell" style="background:rgba(255,255,255,0.02)">
        <div class="ticker-label">Khớp Lệnh</div>
        <div class="ticker-value" style="color:{c_price}">{price:,.0f}</div>
        <div class="ticker-sub" style="color:{c_price}">{change:+,.0f} ({change_pct:+.2f}%)</div>
      </div>
      <div class="ticker-cell">
        <div class="ticker-label">Cao / Thấp</div>
        <div class="ticker-value" style="color:{COLORS['text']}">{high:,.0f} / {low:,.0f}</div>
        <div class="ticker-sub">Biên độ phiên</div>
      </div>
      <div class="ticker-cell">
        <div class="ticker-label">Khối Lượng / GTGD</div>
        <div class="ticker-value" style="color:{COLORS['text']}">{volume:,.0f}</div>
        <div class="ticker-sub">{fmt_vnd(value)}</div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_scorecards(score: dict[str, Any], rec: dict[str, Any], valuation: dict[str, Any], risk: dict[str, Any]) -> None:
    """Khối Scorecards định lượng với Font số lớn, Glassmorphism và Progress Bar trực quan."""
    overall = safe_float(score.get("overall_score"))
    grade = str(score.get("grade", "Ổn định"))
    c_score = score_color(overall)

    action = str(rec.get("action", "THEO DÕI"))
    conviction = str(rec.get("conviction", "Trung bình"))
    c_action = ACTION_COLORS.get(action, COLORS["text"])
    target_p = safe_float(rec.get("target_price"))

    fair_val = safe_float(valuation.get("fair_value"))
    upside = safe_float(valuation.get("upside"))
    c_upside = COLORS["up"] if upside > 0 else COLORS["down"]
    fair_buy = safe_float(valuation.get("fair_buy_price"))

    z_score = safe_float(risk.get("altman", {}).get("z_score"))
    zone = str(risk.get("altman", {}).get("zone", "AN TOÀN"))
    c_zone = ZONE_COLORS.get(zone, COLORS["text"])
    z_meter_pct = min(100.0, max(0.0, (z_score / 4.5) * 100.0))

    sc1, sc2, sc3, sc4 = st.columns(4, gap="small")
    with sc1:
        st.markdown(
            f'<div class="scorecard">'
            f'<div><div class="scorecard-label">Investment Score</div>'
            f'<div class="scorecard-value" style="color:{c_score}">{overall:.1f} <span style="font-size:14px;color:{COLORS["muted"]}">/100</span></div>'
            f'<div class="scorecard-sub"><span class="badge" style="background:{c_score}22;color:{c_score};border:1px solid {c_score}44;">{grade}</span></div></div>'
            f'<div class="mini-meter-track"><div class="mini-meter-fill" style="width:{min(overall, 100):.1f}%;background:{c_score}"></div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with sc2:
        st.markdown(
            f'<div class="scorecard">'
            f'<div><div class="scorecard-label">Khuyến Nghị Định Lượng</div>'
            f'<div class="scorecard-value" style="color:{c_action}">{action}</div>'
            f'<div class="scorecard-sub">Độ tin cậy: <b>{conviction}</b> · Mục tiêu: <b>{target_p:,.0f}</b></div></div>'
            f'<div class="mini-meter-track"><div class="mini-meter-fill" style="width:85%;background:{c_action}"></div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with sc3:
        st.markdown(
            f'<div class="scorecard">'
            f'<div><div class="scorecard-label">Giá Trị Hợp Lý DCF</div>'
            f'<div class="scorecard-value" style="color:{COLORS["text"]}">{fair_val:,.0f} <span style="font-size:12px;color:{c_upside}">({pct(upside):+.1f}%)</span></div>'
            f'<div class="scorecard-sub">Vùng mua an toàn: <b>{fair_buy:,.0f} VNĐ</b></div></div>'
            f'<div class="mini-meter-track"><div class="mini-meter-fill" style="width:{min(max((upside+0.2)*100, 10), 100):.1f}%;background:{c_upside}"></div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with sc4:
        st.markdown(
            f'<div class="scorecard">'
            f'<div><div class="scorecard-label">Altman Z-Score (Sức Bền)</div>'
            f'<div class="scorecard-value" style="color:{c_zone}">{z_score:.2f}</div>'
            f'<div class="scorecard-sub"><span class="badge" style="background:{c_zone}22;color:{c_zone};border:1px solid {c_zone}44;">{zone}</span></div></div>'
            f'<div class="mini-meter-track"><div class="mini-meter-fill" style="width:{z_meter_pct:.1f}%;background:{c_zone}"></div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_pillars(score: dict[str, Any]) -> None:
    """Thanh điểm 5 trụ cột với Glassmorphism."""
    pillars = score.get("pillars", {})
    weights = score.get("weights", {})
    html = ""
    for key in ["fundamental", "valuation", "risk", "quality", "momentum"]:
        val = safe_float(pillars.get(key))
        w = safe_float(weights.get(key)) * 100
        html += (
            f'<div style="margin-bottom:12px;">'
            f'<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">'
            f'<span style="color:#F8FAFC">{PILLAR_LABELS[key]} '
            f'<span style="color:{COLORS["muted"]};font-size:11px">· {w:.0f}%</span></span>'
            f'<span style="font-family:JetBrains Mono,monospace;color:#CBD5E1;font-weight:600;">{val:.1f}</span>'
            f"</div>"
            f'<div style="height:6px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;">'
            f'<div style="width:{min(val, 100):.1f}%;height:100%;background:{score_color(val)};border-radius:3px;"></div>'
            f"</div></div>"
        )
    st.markdown(html, unsafe_allow_html=True)


def render_metrics_12(metrics: list[dict[str, Any]]) -> None:
    """12 chỉ số phân tích cốt lõi chia 2 cột."""
    left, right = st.columns(2, gap="medium")
    for i, m in enumerate(metrics):
        target = left if i % 2 == 0 else right
        with target:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-no">{m["no"]:02d}</div>'
                f'<div class="metric-name">{m["name"]}</div>'
                f'<div class="metric-value">{m["value"]}</div>'
                f'<div class="metric-note">{m["note"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR 240px)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f'<div style="font-size:11px;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:{COLORS["gold"]};margin-bottom:8px;">'
        f'🧭 PHÂN VÙNG PHÂN TÍCH</div>',
        unsafe_allow_html=True,
    )
    nav_options = [
        "📊 Tổng quan",
        "📑 12 Chỉ số Vàng",
        "🏢 Cơ bản & F-Score",
        "💎 Định giá DCF",
        "📈 Kỹ thuật & RSI",
        "🛡️ Rủi ro & Altman Z",
        "🤖 Kịch bản Giá ML",
        "📝 Luận điểm Đầu tư",
        "🔍 Bộ lọc & So sánh",
        "💼 Tối ưu Danh mục",
        "💬 Trợ lý AI",
        "⚙️ Dữ liệu JSON",
    ]
    selected_view = st.radio(
        "Chuyển trang",
        nav_options,
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    with st.expander("⚙️ Tham số Định lượng", expanded=False):
        mode = st.radio(
            "Chế độ kết nối",
            ["Trực tiếp (in-process)", "Qua API Gateway"],
            help="Chế độ trực tiếp không cần chạy uvicorn.",
        )
        api_url = app_config.api_base_url
        if mode == "Qua API Gateway":
            api_url = st.text_input("Địa chỉ API", value=app_config.api_base_url)

        rf = st.slider("Lãi suất phi rủi ro (Rf)", 0.0, 0.10,
                       float(finance_config.risk_free_rate), 0.005, format="%.3f")
        erp = st.slider("Phần bù rủi ro vốn (ERP)", 0.02, 0.15,
                        float(finance_config.equity_risk_premium), 0.005, format="%.3f")
        g_terminal = st.slider("Tăng trưởng dài hạn (g)", 0.0, 0.06,
                               float(finance_config.terminal_growth), 0.005, format="%.3f")
        tax = st.slider("Thuế suất TNDN", 0.0, 0.35,
                        float(finance_config.corporate_tax_rate), 0.01, format="%.2f")

    st.markdown("---")
    auto_refresh = st.checkbox("🔄 Auto Refresh Realtime (5s)", value=False)
    if auto_refresh:
        import time
        time.sleep(5)
        st.rerun()

    from Module1.data_source import get_data_source
    active_src = get_data_source().active_source
    src_ok = (active_src != "MOCK")
    source_label = "SSI FastConnect v2" if active_src == "SSI" else ("Vnstock 4.x" if active_src == "Vnstock" else "Mock Data")


# ---------------------------------------------------------------------------
# THU THẬP DỮ LIỆU & PHÂN TÍCH
# ---------------------------------------------------------------------------
if "last_symbol" not in st.session_state:
    st.session_state.last_symbol = "FPT"

symbol = st.session_state.last_symbol
user_name = st.session_state.get("username", "Admin")

# Render Fixed Top Navigation Bar
render_top_navbar(symbol, source_label, user_name)

try:
    with st.spinner(f"Đang phân tích định lượng cho {symbol}..."):
        if mode == "Qua API Gateway":
            data = analyze_via_api(symbol, api_url)
        else:
            data = analyze_direct(symbol, rf, erp, g_terminal, tax)
except requests.RequestException:
    st.error(
        f"Không kết nối được API Gateway tại {api_url}. "
        "Khởi động bằng lệnh `uvicorn main:app --reload --port 8000`, "
        "hoặc chuyển sang chế độ Trực tiếp ở tham số định lượng."
    )
    st.stop()
except Exception as exc:  # noqa: BLE001
    st.error(f"Không phân tích được {symbol}: {exc}")
    st.stop()

quote = data.get("quote", {})
fundamentals = data.get("fundamentals", {})
valuation = data.get("valuation", {})
technical = data.get("technical", {})
risk = data.get("risk", {})
scenarios = data.get("scenarios", {})
score = data.get("investment_score", {})
rec = data.get("recommendation", {})
journal = data.get("thesis_journal", {})
elapsed_ms = int(data.get("elapsed_ms", 0))
data_source = str(data.get("data_source", "SSI"))

# Render Company Header with large display font
render_company_header(symbol, quote, elapsed_ms, data_source)

# Render Seamless Ticker Strip
render_ticker_strip(quote)

# Render Quantitative Scorecards
render_scorecards(score, rec, valuation, risk)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# ĐIỀU HƯỚNG NỘI DUNG CHÍNH (MAIN CANVAS)
# ---------------------------------------------------------------------------

# ============================ 1. TỔNG QUAN ================================
if selected_view == "📊 Tổng quan":
    left, right = st.columns([1.55, 1], gap="medium")

    with left:
        st.markdown("**Diễn biến giá & khối lượng kỹ thuật**")
        st.plotly_chart(candlestick_chart(technical), use_container_width=True)

    with right:
        st.markdown("**Điểm số phân rã 5 trụ cột**")
        render_pillars(score)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        st.markdown("**Dự báo 3 kịch bản giá (Machine Learning)**")
        st.plotly_chart(scenario_chart(scenarios), use_container_width=True)

    st.markdown("---")
    st.markdown("**Luận điểm định lượng tóm tắt**")
    for line in rec.get("rationale", []):
        st.markdown(f"- {line}")

    rr1, rr2, rr3, rr4 = st.columns(4)
    rr1.metric("Giá mục tiêu", f"{safe_float(rec.get('target_price')):,.0f} VNĐ")
    rr2.metric("Cắt lỗ tự động (-10%)", f"{safe_float(rec.get('stop_price')):,.0f} VNĐ")
    rr3.metric("Tỷ lệ Lợi nhuận / Rủi ro", f"{safe_float(rec.get('risk_reward_ratio')):.2f}x")
    rr4.metric("Tỷ trọng đề xuất", f"{safe_float(rec.get('position_size_pct')):.2f}% NAV")

# ============================ 2. 12 CHỈ SỐ VÀNG ==========================
elif selected_view == "📑 12 Chỉ số Vàng":
    st.markdown("### 📑 12 Chỉ Số Phân Tích Tài Chính Cốt Lõi")
    st.caption("Tổng hợp tự động từ mô hình định lượng và dữ liệu BCTC chuẩn hóa.")
    render_metrics_12(data.get("metrics_12", []))

# ============================ 3. CƠ BẢN & F-SCORE ========================
elif selected_view == "🏢 Cơ bản & F-Score":
    f = fundamentals
    a, b, c, d = st.columns(4)
    a.metric("Biên lợi nhuận gộp", f"{pct(f.get('gross_margin')):.2f}%")
    b.metric("Biên EBIT", f"{pct(f.get('ebit_margin')):.2f}%")
    c.metric("Biên lợi nhuận ròng", f"{pct(f.get('net_margin')):.2f}%")
    d.metric("CFO / LNST", f"{safe_float(f.get('cfo_to_net_income')):.2f}x")

    a, b, c, d = st.columns(4)
    a.metric("ROE", f"{pct(f.get('roe')):.2f}%")
    b.metric("ROA", f"{pct(f.get('roa')):.2f}%")
    c.metric("ROIC", f"{pct(f.get('roic')):.2f}%")
    d.metric("Nợ vay / VCSH", f"{safe_float(f.get('debt_to_equity')):.2f}x")

    a, b, c, d = st.columns(4)
    a.metric("Doanh thu TTM", fmt_vnd(f.get("revenue_ttm")))
    b.metric("LNST TTM", fmt_vnd(f.get("net_income_ttm")))
    c.metric("Dòng tiền tự do (FCF)", fmt_vnd(f.get("free_cash_flow")))
    d.metric("Tăng trưởng DT (CAGR)", f"{pct(f.get('revenue_cagr')):.2f}%")

    st.markdown("---")
    st.markdown("**Diễn biến kết quả kinh doanh theo quý**")
    st.plotly_chart(financial_history_chart(f.get("history", [])), use_container_width=True)

    with st.expander("Bảng số liệu chi tiết các quý gần nhất"):
        hist = f.get("history", [])
        if hist:
            df = pd.DataFrame(hist)
            df.columns = ["Kỳ", "Doanh thu", "EBIT", "LNST", "CFO", "Biên LN ròng", "Biên EBIT"]
            st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    f_score_data = f.get("piotroski_f_score", {})
    f_val = int(f_score_data.get("score", 0))
    f_rating = str(f_score_data.get("rating", "Ổn định"))
    f_color = COLORS["up"] if f_val >= 8 else (COLORS["reference"] if f_val >= 5 else COLORS["down"])

    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        st.markdown(
            f'<div class="glass-panel" style="text-align:center;">'
            f'<div style="font-size:11px;color:{COLORS["muted"]};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Piotroski F-Score</div>'
            f'<div style="font-size:38px;font-weight:800;color:{f_color};line-height:1;">{f_val} <span style="font-size:16px;color:{COLORS["muted"]}">/ 9</span></div>'
            f'<div style="margin-top:8px;"><span class="badge" style="background:{f_color}22;color:{f_color};border:1px solid {f_color}44;">{f_rating}</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_f2:
        st.markdown("**Kiểm định 9 bài test kế toán:**")
        crit = f_score_data.get("criteria", {})
        c_items = [
            ("ROA > 0 (Sinh lời tài sản dương)", crit.get("roa_positive")),
            ("CFO > 0 (Dòng tiền kinh doanh dương)", crit.get("cfo_positive")),
            ("Tăng trưởng ROA dương", crit.get("roa_growth")),
            ("Chất lượng LN: CFO > LNST", crit.get("accrual_quality")),
            ("Đòn bẩy nợ dài hạn giảm", crit.get("leverage_down")),
            ("Hệ số thanh toán hiện hành tăng", crit.get("liquidity_up")),
            ("Không pha loãng cổ phiếu", crit.get("no_dilution")),
            ("Biên lợi nhuận gộp tăng", crit.get("gross_margin_up")),
            ("Vòng quay tài sản tăng", crit.get("asset_turnover_up")),
        ]
        col_ca, col_cb = st.columns(2)
        for idx, (label, passed) in enumerate(c_items):
            icon = "✅" if passed else "❌"
            color_txt = COLORS["up"] if passed else COLORS["down"]
            target_col = col_ca if idx % 2 == 0 else col_cb
            target_col.markdown(f"{icon} <span style='color:{color_txt}'>{label}</span>", unsafe_allow_html=True)

# ============================ 4. ĐỊNH GIÁ DCF ============================
elif selected_view == "💎 Định giá DCF":
    v = valuation
    dcf = v.get("dcf", {})
    wacc_det = v.get("wacc_detail", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Giá trị nội tại (DCF)", f"{safe_float(v.get('intrinsic_value')):,.0f} VNĐ")
    c2.metric("Chi phí vốn (WACC)", f"{pct(v.get('wacc')):.2f}%")
    c3.metric("Tăng trưởng dài hạn (g)", f"{pct(v.get('terminal_growth')):.2f}%")

    col_l, col_r = st.columns(2, gap="medium")
    with col_l:
        st.markdown("**Cơ cấu chi phí vốn WACC**")
        st.plotly_chart(wacc_chart(wacc_det), use_container_width=True)

    with col_r:
        st.markdown("**Dự báo dòng tiền tự do (FCF) 5 năm**")
        st.plotly_chart(dcf_chart(dcf), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🌡️ Ma Trận Độ Nhạy Định Giá DCF 2 Chiều (Valuation Heatmap)")
    st.caption("Khảo sát thị giá nội tại khi Chi phí vốn (WACC) và Tăng trưởng dài hạn (g) biến động.")
    sens = v.get("sensitivity", {})
    if sens:
        st.plotly_chart(dcf_sensitivity_heatmap(sens, safe_float(v.get("price"))), use_container_width=True)

    st.markdown("---")
    st.markdown("**Định giá tương đối (Bội số ngành)**")
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("P/E (TTM)", f"{safe_float(v.get('pe')):.2f}x")
    v2.metric("P/E trung vị ngành", f"{safe_float(v.get('peer_pe')):.2f}x")
    v3.metric("P/B", f"{safe_float(v.get('pb')):.2f}x")
    v4.metric("P/B trung vị ngành", f"{safe_float(v.get('peer_pb')):.2f}x")

# ============================ 5. KỸ THUẬT & RSI ==========================
elif selected_view == "📈 Kỹ thuật & RSI":
    t = technical
    summary = t.get("summary", {})
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Xu hướng chính", str(summary.get("trend", "")))
    t2.metric("RSI (14) Wilder", f"{safe_float(summary.get('rsi14')):.1f}")
    t3.metric("Hỗ trợ kỹ thuật", f"{safe_float(summary.get('support_level')):,.0f} VNĐ")
    t4.metric("Kháng cự kỹ thuật", f"{safe_float(summary.get('resistance_level')):,.0f} VNĐ")

    st.markdown("---")
    st.markdown("**Động lượng RSI(14) Wilder & MACD (12-26-9)**")
    st.plotly_chart(momentum_chart(t, months=6), use_container_width=True)

    st.markdown("---")
    st.markdown("**Mức độ sụt giảm từ đỉnh (Drawdown)**")
    st.plotly_chart(drawdown_chart(t), use_container_width=True)

# ============================ 6. RỦI RO & ALTMAN Z ========================
elif selected_view == "🛡️ Rủi ro & Altman Z":
    r = risk
    alt = r.get("altman", {})
    mkt = r.get("market_risk", {})

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Altman Z-Score", f"{safe_float(alt.get('z_score')):.2f}", str(alt.get("zone", "")))
    r2.metric("Beta (VNINDEX)", f"{safe_float(mkt.get('beta')):.2f}")
    r3.metric("Biến động năm", f"{pct(mkt.get('annual_volatility')):.2f}%")
    r4.metric("Max Drawdown 1 năm", f"{pct(mkt.get('max_drawdown_1y')):.2f}%")

    st.markdown("---")
    st.markdown("**Phân rã 5 biến số mô hình phá sản Altman Z-Score:**")
    comp = alt.get("components", {})
    cols = st.columns(5)
    cols[0].metric("X1 (Vốn LĐ / TS)", f"{safe_float(comp.get('X1_wc_to_assets')):.3f}")
    cols[1].metric("X2 (LN giữ lại / TS)", f"{safe_float(comp.get('X2_re_to_assets')):.3f}")
    cols[2].metric("X3 (EBIT / TS)", f"{safe_float(comp.get('X3_ebit_to_assets')):.3f}")
    cols[3].metric("X4 (VCSH / Nợ)", f"{safe_float(comp.get('X4_equity_to_debt')):.3f}")
    cols[4].metric("X5 (Doanh thu / TS)", f"{safe_float(comp.get('X5_sales_to_assets')):.3f}")

    st.markdown("---")
    st.markdown("### 🛡️ Beneish M-Score (Cảnh Báo Thao Túng Báo Cáo Tài Chính)")
    st.caption("Mô hình 8 biến số của GS. Messod Beneish phát hiện hành vi bóp méo số liệu kế toán.")

    beneish_data = r.get("beneish", {})
    b_score = safe_float(beneish_data.get("m_score", -99.0))
    b_risk = str(beneish_data.get("risk", "AN TOÀN"))
    b_color = COLORS["down"] if b_risk == "NGUY CƠ CAO" else (COLORS["reference"] if b_risk == "CẢNH BÁO" else COLORS["up"])

    col_b1, col_b2 = st.columns([1, 2.2])
    with col_b1:
        st.markdown(
            f'<div class="glass-panel" style="text-align:center;">'
            f'<div style="font-size:11px;color:{COLORS["muted"]};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Beneish M-Score</div>'
            f'<div style="font-size:36px;font-weight:800;color:{b_color};line-height:1.1;">{b_score:.2f}</div>'
            f'<div style="margin-top:8px;"><span class="badge" style="background:{b_color}22;color:{b_color};border:1px solid {b_color}44;">{b_risk}</span></div>'
            f'<div style="font-size:11px;color:{COLORS["muted"]};margin-top:8px;">Ngưỡng an toàn: M &le; -1.78</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_b2:
        b_vars = beneish_data.get("variables", {})
        if b_vars:
            df_b = pd.DataFrame([
                {"Biến số": "DSRI (Chỉ số Phải thu)", "Giá trị": f"{safe_float(b_vars.get('DSRI')):.3f}", "Chuẩn": "< 1.0 (An toàn)"},
                {"Biến số": "GMI (Chỉ số Biên gộp)", "Giá trị": f"{safe_float(b_vars.get('GMI')):.3f}", "Chuẩn": "< 1.0 (Lành mạnh)"},
                {"Biến số": "AQI (Chất lượng tài sản)", "Giá trị": f"{safe_float(b_vars.get('AQI')):.3f}", "Chuẩn": "< 1.0 (Không vốn hóa CP)"},
                {"Biến số": "SGI (Tăng trưởng doanh thu)", "Giá trị": f"{safe_float(b_vars.get('SGI')):.3f}", "Chuẩn": "Tăng trưởng tự nhiên"},
                {"Biến số": "DEPI (Tỷ lệ khấu hao)", "Giá trị": f"{safe_float(b_vars.get('DEPI')):.3f}", "Chuẩn": "~ 1.0 (Khấu hao ổn định)"},
                {"Biến số": "SGAI (Chi phí BH & QL)", "Giá trị": f"{safe_float(b_vars.get('SGAI')):.3f}", "Chuẩn": "< 1.0 (Kiểm soát chi phí)"},
                {"Biến số": "LVGI (Đòn bẩy tài chính)", "Giá trị": f"{safe_float(b_vars.get('LVGI')):.3f}", "Chuẩn": "< 1.0 (Không tăng đòn bẩy)"},
                {"Biến số": "TATA (Dồn tích tổng thể)", "Giá trị": f"{safe_float(b_vars.get('TATA')):.3f}", "Chuẩn": "< 0 (Dòng tiền > LN)"},
            ])
            st.dataframe(df_b, use_container_width=True, hide_index=True)

# ============================ 7. KỊCH BẢN GIÁ ML ==========================
elif selected_view == "🤖 Kịch bản Giá ML":
    st.markdown("### 🤖 Dự Báo 3 Kịch Bản Giá Bằng Machine Learning")
    st.caption("Ứng dụng mô hình Random Forest Regressor với khoảng tin cậy 95% (±1.96σ).")

    sc_col1, sc_col2 = st.columns([1.5, 1], gap="medium")
    with sc_col1:
        st.plotly_chart(scenario_chart(scenarios), use_container_width=True)
    with sc_col2:
        st.markdown(
            f'<div class="glass-panel">'
            f'<div style="font-size:14px;font-weight:700;color:{COLORS["gold"]};margin-bottom:8px;">Chi tiết 3 kịch bản giá:</div>'
            f'<div style="margin-bottom:8px;">🔴 <b>Bear Case (Kịch bản xấu):</b> {safe_float(scenarios.get("bear_case")):,.0f} VNĐ ({pct(scenarios.get("bear_return")):.2f}%)</div>'
            f'<div style="margin-bottom:8px;">🟡 <b>Base Case (Kịch bản cơ sở):</b> {safe_float(scenarios.get("base_case")):,.0f} VNĐ ({pct(scenarios.get("base_return")):.2f}%)</div>'
            f'<div style="margin-bottom:8px;">🟢 <b>Bull Case (Kịch bản tốt):</b> {safe_float(scenarios.get("bull_case")):,.0f} VNĐ ({pct(scenarios.get("bull_return")):.2f}%)</div>'
            f'<div style="font-size:11px;color:{COLORS["muted"]};margin-top:12px;">Độ lệch chuẩn &sigma; = {safe_float(scenarios.get("sigma")):,.0f} VNĐ</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    meta = scenarios.get("meta", {})
    st.caption(
        f"Thuật toán: {meta.get('model', 'RandomForestRegressor')} · "
        f"Chân trời: {meta.get('horizon_days', 20)} phiên · "
        f"Mẫu huấn luyện: {meta.get('train_samples', 0)} phiên · "
        f"Hệ số R²: {meta.get('r2_in_sample', 'n/a')}"
    )

# ============================ 8. LUẬN ĐIỂM ĐẦU TƯ =========================
elif selected_view == "📝 Luận điểm Đầu tư":
    st.markdown("### 📝 Nhật Ký Luận Điểm Đầu Tư (Investment Thesis Journal)")
    md = journal.get("markdown", "")
    if md:
        st.markdown(md)
    else:
        st.info("Chưa có nhật ký luận điểm cho mã này.")

# ============================ 9. BỘ LỌC & SO SÁNH =========================
elif selected_view == "🔍 Bộ lọc & So sánh":
    st.markdown("### 🔍 Bộ Lọc & So Sánh Cổ Phiếu Đa Mã (Stock Screener)")
    st.caption("Quét và so sánh đồng thời các cổ phiếu theo Investment Score, định giá và chỉ số sức khỏe tài chính.")

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        screener_input = st.text_input("Danh sách mã cổ phiếu cần quét (phân cách bằng dấu phẩy):",
                                       value="FPT, HPG, VNM, MWG, VCB, SSI", key="screener_tickers")
    with col_s2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        btn_scan = st.button("🚀 Bắt đầu Quét", use_container_width=True, type="primary")

    ticker_list = [s.strip().upper() for s in screener_input.split(",") if s.strip()]

    if btn_scan:
        screener_rows = []
        radar_data: dict[str, dict[str, float]] = {}
        with st.spinner("Đang quét dữ liệu định lượng đa mã..."):
            from Module6.decision_engine import get_engine
            screener_engine = get_engine(finance_config)
            for t_sym in ticker_list:
                try:
                    res = screener_engine.analyze(t_sym)
                    sc = res.get("investment_score", {})
                    va = res.get("valuation", {})
                    fu = res.get("fundamentals", {})
                    ri = res.get("risk", {})
                    reco = res.get("recommendation", {})
                    screener_rows.append({
                        "Mã CP": t_sym,
                        "Điểm Đầu Tư": safe_float(sc.get("overall_score")),
                        "Xếp loại": str(sc.get("grade", "")),
                        "Khuyến nghị": str(reco.get("action", "")),
                        "Giá HT (VNĐ)": safe_float(res.get("quote", {}).get("price")),
                        "P/E": safe_float(va.get("pe")),
                        "ROE (%)": pct(fu.get("roe")),
                        "Biên EBIT (%)": pct(fu.get("ebit_margin")),
                        "Piotroski F": int(fu.get("piotroski_f_score", {}).get("score", 0)),
                        "Altman Z": safe_float(ri.get("altman", {}).get("z_score")),
                        "Beneish M": safe_float(ri.get("beneish", {}).get("m_score")),
                    })
                    radar_data[t_sym] = sc.get("pillars", {})
                except Exception:
                    pass

        if screener_rows:
            df_screener = pd.DataFrame(screener_rows).sort_values(by="Điểm Đầu Tư", ascending=False)
            st.dataframe(df_screener, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("**Biểu đồ Radar So Sánh 5 Trụ Cột Đa Mã**")
            st.plotly_chart(multi_ticker_radar_chart(radar_data), use_container_width=True)

# ============================ 10. TỐI ƯU DANH MỤC ========================
elif selected_view == "💼 Tối ưu Danh mục":
    st.markdown("### 💼 Tối Ưu Hóa Danh Mục Đầu Tư Markowitz (Efficient Frontier)")
    st.caption("Ứng dụng mô phỏng Monte Carlo 1,000 kịch bản để tìm đường biên hiệu quả và phân bổ vốn tối ưu.")

    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        port_input = st.text_input("Nhập danh mục cổ phiếu (3 đến 6 mã):", value="FPT, HPG, VNM, MWG", key="port_tickers")
    with col_p2:
        capital_input = st.number_input("Tổng vốn đầu tư (VNĐ):", min_value=10_000_000, value=100_000_000, step=10_000_000, format="%d")

    port_syms = [s.strip().upper() for s in port_input.split(",") if s.strip()]

    if st.button("⚖️ Chạy Tối Ưu Hóa Tỷ Trọng", use_container_width=True, type="primary"):
        with st.spinner("Đang tải dữ liệu chuỗi giá và mô phỏng 1,000 danh mục Monte Carlo..."):
            from Module1.data_source import get_data_source
            from common.utils import to_returns
            from Module5.risk_engine import RiskEngine

            ds = get_data_source()
            returns_dict = {}
            valid_syms = []
            for s in port_syms:
                try:
                    ohlc_data = ds.get_ohlc(s)
                    closes = [safe_float(r.get("close")) for r in ohlc_data]
                    rets = to_returns(closes).tolist()
                    if len(rets) >= 20:
                        returns_dict[s] = rets
                        valid_syms.append(s)
                except Exception:
                    pass

            if len(valid_syms) >= 2:
                opt_res = RiskEngine.optimize_portfolio(returns_dict, risk_free_rate=finance_config.risk_free_rate)
                st.plotly_chart(efficient_frontier_chart(opt_res), use_container_width=True)

                col_res1, col_res2 = st.columns(2, gap="large")
                with col_res1:
                    max_s = opt_res.get("max_sharpe", {})
                    st.success(f"★ **Danh mục Tối ưu Sharpe Ratio ({safe_float(max_s.get('sharpe')):.2f})**")
                    st.write(f"- Lợi suất kỳ vọng năm: **{pct(max_s.get('return')):.2f}%**")
                    st.write(f"- Biến động rủi ro năm: **{pct(max_s.get('volatility')):.2f}%**")
                    w_s = max_s.get("weights", {})
                    alloc_s = []
                    for sym_name, wt in w_s.items():
                        alloc_vnd = capital_input * wt
                        alloc_s.append({"Mã CP": sym_name, "Tỷ trọng": f"{wt*100:.1f}%", "Vốn phân bổ": f"{alloc_vnd:,.0f} VNĐ"})
                    st.dataframe(pd.DataFrame(alloc_s), use_container_width=True, hide_index=True)

                with col_res2:
                    min_v = opt_res.get("min_volatility", {})
                    st.info(f"● **Danh mục Rủi ro Tối thiểu (Biến động {pct(min_v.get('volatility')):.2f}%)**")
                    st.write(f"- Lợi suất kỳ vọng năm: **{pct(min_v.get('return')):.2f}%**")
                    st.write(f"- Sharpe Ratio: **{safe_float(min_v.get('sharpe')):.2f}**")
                    w_v = min_v.get("weights", {})
                    alloc_v = []
                    for sym_name, wt in w_v.items():
                        alloc_vnd = capital_input * wt
                        alloc_v.append({"Mã CP": sym_name, "Tỷ trọng": f"{wt*100:.1f}%", "Vốn phân bổ": f"{alloc_vnd:,.0f} VNĐ"})
                    st.dataframe(pd.DataFrame(alloc_v), use_container_width=True, hide_index=True)
            else:
                st.error("Cần tối thiểu 2 mã cổ phiếu có đủ dữ liệu chuỗi giá để tối ưu danh mục.")

# ============================ 11. TRỢ LÝ AI ===============================
elif selected_view == "💬 Trợ lý AI":
    st.markdown(f"### 💬 Trợ Lý AI Định Lượng ({symbol})")
    st.caption("Đàm thoại thông minh với AI am hiểu dữ liệu tài chính, định giá DCF và chỉ số kỹ thuật.")

    try:
        from chatbot_bot import StockChatBot
        bot = StockChatBot()
    except Exception as exc:
        st.error(f"Không thể khởi tạo StockChatBot: {exc}")
        bot = None

    if bot:
        if "chat_symbol" not in st.session_state or st.session_state.chat_symbol != symbol:
            st.session_state.chat_symbol = symbol
            st.session_state.chat_history = []
        elif "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for role, msg in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(msg)

        st.markdown("**Gợi ý câu hỏi nhanh:**")
        q_cols = st.columns(3)
        preset_questions = [
            f"Đánh giá tổng quan tiềm năng đầu tư mã {symbol}?",
            f"Mức định giá DCF và P/E của {symbol} có hấp dẫn không?",
            f"Các rủi ro chính và ngưỡng cắt lỗ của {symbol} là gì?",
        ]
        selected_preset = None
        for idx, q_text in enumerate(preset_questions):
            if q_cols[idx].button(q_text, key=f"preset_btn_{idx}"):
                selected_preset = q_text

        user_query = st.chat_input(f"Đặt câu hỏi cho Trợ lý AI về {symbol}...") or selected_preset

        if user_query:
            st.session_state.chat_history.append(("user", user_query))
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                with st.spinner("AI đang suy luận dữ liệu..."):
                    reply = bot.ask(user_query, context_data=data)
                st.markdown(reply)
                st.session_state.chat_history.append(("assistant", reply))

            if selected_preset:
                st.rerun()

# ============================ 12. DỮ LIỆU JSON ===========================
elif selected_view == "⚙️ Dữ liệu JSON":
    st.markdown("### ⚙️ Dữ Liệu Raw JSON Payload")
    st.caption("Dữ liệu thô đồng bộ trực tiếp với API Gateway RESTful endpoint.")
    st.code(f"GET {app_config.api_base_url}/api/v1/analyze/{symbol}", language="bash")
    st.json(data, expanded=False)

# --- Chân trang ---
st.markdown(
    f'<div class="footnote">'
    f"Toàn bộ số liệu do hệ thống tự động tính toán từ dữ liệu thô: mô hình DCF/WACC, "
    f"Altman Z-Score, Piotroski F-Score, Beneish M-Score và Random Forest Regressor. "
    f"Kết quả là đầu ra định lượng phục vụ tham khảo, không phải khuyến nghị đầu tư được cấp phép. "
    f"Người dùng chịu trách nhiệm với quyết định giao dịch của mình.</div>",
    unsafe_allow_html=True,
)