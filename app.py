"""
app.py
GIAO DIỆN STREAMLIT — AI Financial & Investment Intelligence Platform

Chạy:
    streamlit run app.py

Hai chế độ kết nối:
    - Trực tiếp: gọi thẳng DecisionEngine trong cùng tiến trình (không cần
      bật API Gateway) — phù hợp khi phát triển trong VS Code.
    - Qua API Gateway: gọi http://localhost:8000/api/v1/analyze/{symbol}
      — phù hợp khi triển khai tách tầng.

Tầng giao diện KHÔNG chứa logic tài chính: mọi con số đều lấy nguyên từ
payload JSON của Module 6.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
import requests
import streamlit as st

from common.utils import fmt_vnd, pct, safe_float
from config import app_config, finance_config
from ui.charts import (
    candlestick_chart,
    dcf_chart,
    drawdown_chart,
    financial_history_chart,
    momentum_chart,
    pillar_chart,
    scenario_chart,
    wacc_chart,
)
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
# Tầng dữ liệu
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

    return DecisionEngine().analyze(symbol)


@st.cache_data(ttl=120, show_spinner=False)
def analyze_via_api(symbol: str, base_url: str) -> dict[str, Any]:
    """Gọi API Gateway."""
    url = f"{base_url.rstrip('/')}/api/v1/analyze/{symbol}"
    resp = requests.get(url, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"API trả về {resp.status_code}: {resp.text[:200]}")
    return resp.json()


# ---------------------------------------------------------------------------
# Thành phần giao diện
# ---------------------------------------------------------------------------
def render_price_board(quote: dict[str, Any]) -> None:
    """Dải bảng giá theo đúng quy ước màu bảng điện HOSE."""
    price = safe_float(quote.get("price"))
    ref = safe_float(quote.get("ref_price"))
    ceiling = safe_float(quote.get("ceiling"))
    floor = safe_float(quote.get("floor"))
    change = safe_float(quote.get("change"))
    change_pct = safe_float(quote.get("change_pct"))
    c_price = price_color(price, ref, ceiling, floor)

    cells = [
        ("Trần", f"{ceiling:,.0f}", "", COLORS["ceiling"]),
        ("Tham chiếu", f"{ref:,.0f}", "", COLORS["reference"]),
        ("Sàn", f"{floor:,.0f}", "", COLORS["floor"]),
        ("Khớp lệnh", f"{price:,.0f}", f"{change:+,.0f} ({change_pct:+.2f}%)", c_price),
        ("Cao / Thấp", f"{safe_float(quote.get('high')):,.0f}",
         f"{safe_float(quote.get('low')):,.0f}", COLORS["text"]),
        ("Khối lượng", f"{safe_float(quote.get('volume')):,.0f}",
         fmt_vnd(quote.get("value")), COLORS["text"]),
    ]

    html = '<div class="price-board">'
    for label, value, sub, color in cells:
        html += (
            f'<div class="pb-cell">'
            f'<div class="pb-label">{label}</div>'
            f'<div class="pb-value" style="color:{color}">{value}</div>'
            f'<div class="pb-sub">{sub}</div>'
            f"</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def kpi(label: str, value: str, note: str = "", color: str | None = None) -> str:
    color = color or COLORS["text"]
    return (
        f'<div class="kpi">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color:{color}">{value}</div>'
        f'<div class="kpi-note">{note}</div>'
        f"</div>"
    )


def render_pillars(score: dict[str, Any]) -> None:
    """Thanh điểm 5 trụ cột dạng HTML gọn (dùng trong cột hẹp)."""
    pillars = score.get("pillars", {})
    weights = score.get("weights", {})
    html = ""
    for key in ["fundamental", "valuation", "risk", "quality", "momentum"]:
        val = safe_float(pillars.get(key))
        w = safe_float(weights.get(key)) * 100
        html += (
            f'<div class="pillar-row">'
            f'<div class="pillar-top">'
            f'<span class="pillar-name">{PILLAR_LABELS[key]} '
            f'<span style="color:{COLORS["muted"]};font-size:11px">· {w:.0f}%</span></span>'
            f'<span class="pillar-num">{val:.1f}</span>'
            f"</div>"
            f'<div class="pillar-track">'
            f'<div class="pillar-fill" style="width:{min(val, 100):.1f}%;'
            f'background:{score_color(val)}"></div>'
            f"</div></div>"
        )
    st.markdown(html, unsafe_allow_html=True)


def render_metrics_12(metrics: list[dict[str, Any]]) -> None:
    """12 chỉ số phân tích cốt lõi, chia 2 cột."""
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


def badge(text: str, color: str) -> str:
    return (f'<span class="badge" style="background:{color}22;color:{color};'
            f'border:1px solid {color}55">{text}</span>')


# ---------------------------------------------------------------------------
# Thanh bên
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f'<div style="font-size:15px;font-weight:800;letter-spacing:-0.02em;'
        f'line-height:1.35;margin-bottom:2px">AI FINANCIAL<br>'
        f'<span style="color:{COLORS["accent"]}">& INVESTMENT INTELLIGENCE</span></div>'
        f'<div style="font-size:11px;color:{COLORS["muted"]};margin-bottom:18px">'
        f"Phân tích đầu tư định lượng · Thị trường Việt Nam</div>",
        unsafe_allow_html=True,
    )

    symbol_input = st.text_input("Mã chứng khoán", value="FPT", max_chars=10).upper().strip()
    run = st.button("Phân tích", type="primary")

    st.markdown("---")
    mode = st.radio(
        "Chế độ kết nối",
        ["Trực tiếp (in-process)", "Qua API Gateway"],
        help="Chế độ trực tiếp không cần chạy uvicorn.",
    )
    api_url = app_config.api_base_url
    if mode == "Qua API Gateway":
        api_url = st.text_input("Địa chỉ API", value=app_config.api_base_url)

    st.markdown("---")
    st.markdown("**Tham số định giá**")
    rf = st.slider("Lãi suất phi rủi ro (Rf)", 0.0, 0.10,
                   float(finance_config.risk_free_rate), 0.005, format="%.3f")
    erp = st.slider("Phần bù rủi ro vốn cổ phần (ERP)", 0.02, 0.15,
                    float(finance_config.equity_risk_premium), 0.005, format="%.3f")
    g_terminal = st.slider("Tăng trưởng dài hạn (g)", 0.0, 0.06,
                           float(finance_config.terminal_growth), 0.005, format="%.3f")
    tax = st.slider("Thuế suất TNDN", 0.0, 0.35,
                    float(finance_config.corporate_tax_rate), 0.01, format="%.2f")

    st.markdown("---")
    from Module1.data_source import get_data_source
    active_src = get_data_source().active_source
    src_ok = (active_src != "MOCK")
    source_label = "SSI FastConnect Data v2" if active_src == "SSI" else ("Vnstock 4.x (Real Data)" if active_src == "Vnstock" else "Dữ liệu mô phỏng (Mock)")

    st.markdown(
        f'<div style="font-size:11.5px;color:{COLORS["muted"]}">Nguồn dữ liệu<br>'
        f'<span style="color:{COLORS["up"] if src_ok else COLORS["reference"]};'
        f'font-weight:600">'
        f'{source_label}</span></div>',
        unsafe_allow_html=True,
    )
    if not src_ok:
        st.caption("Khai báo SSI_CONSUMER_ID hoặc bật VNSTOCK_ENABLED trong file .env để dùng dữ liệu thật.")


# ---------------------------------------------------------------------------
# Thân trang
# ---------------------------------------------------------------------------
if "last_symbol" not in st.session_state:
    st.session_state.last_symbol = "FPT"
if run and symbol_input:
    st.session_state.last_symbol = symbol_input

symbol = st.session_state.last_symbol

if not symbol:
    st.info("Nhập mã chứng khoán ở thanh bên để bắt đầu phân tích.")
    st.stop()

try:
    with st.spinner(f"Đang thu thập dữ liệu và chạy mô hình cho {symbol}..."):
        if mode == "Qua API Gateway":
            data = analyze_via_api(symbol, api_url)
        else:
            data = analyze_direct(symbol, rf, erp, g_terminal, tax)
except requests.RequestException:
    st.error(
        f"Không kết nối được API Gateway tại {api_url}. "
        "Khởi động bằng lệnh `uvicorn main:app --reload --port 8000`, "
        "hoặc chuyển sang chế độ Trực tiếp ở thanh bên."
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

# --- Tiêu đề ---
import datetime

# Lấy thời gian thực tế hiện tại (Giờ : Phút : Giây)
now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# --- Tiêu đề Realtime ---
st.markdown(
    f'<div class="symbol-head">'
    f'<span class="symbol-code">{data.get("symbol", symbol)}</span>'
    f'<span class="symbol-meta">{quote.get("exchange", "HOSE")} · '
    f'cập nhật 🔴 <b>{now_str}</b> · nguồn <b>{data.get("data_source", "SSI")}</b> · '
    f'xử lý {data.get("elapsed_ms", 0)} ms</span>'
    f"</div>",
    unsafe_allow_html=True,
)

# Thêm nút Tải lại dữ liệu & Tùy chọn Tự động Refresh Realtime ở Sidebar/Header
with st.sidebar:
    st.markdown("---")
    auto_refresh = st.checkbox("🔄 Auto Refresh Realtime (5s)", value=False)
    if auto_refresh:
        import time
        time.sleep(5)
        st.rerun()

for w in data.get("warnings", []):
    if "Endpoint BCTC không khả dụng" in w:
        continue  # Bỏ qua cảnh báo BCTC
    st.warning(w, icon="⚠️")

render_price_board(quote)

# --- Hàng KPI ---
overall = safe_float(score.get("overall_score"))
action = str(rec.get("action", ""))
zone = risk.get("altman", {}).get("zone", "")
upside = safe_float(valuation.get("upside"))

c1, c2, c3, c4, c5 = st.columns(5, gap="small")
with c1:
    st.markdown(kpi("Investment Score", f"{overall:.1f}",
                    str(score.get("grade", "")), score_color(overall)),
                unsafe_allow_html=True)
with c2:
    st.markdown(kpi("Khuyến nghị", action,
                    f"Độ tin cậy: {rec.get('conviction', '')}",
                    ACTION_COLORS.get(action, COLORS["text"])),
                unsafe_allow_html=True)
with c3:
    st.markdown(kpi("Giá trị hợp lý", f"{safe_float(valuation.get('fair_value')):,.0f}",
                    f"DCF {safe_float(valuation.get('intrinsic_value')):,.0f} · "
                    f"So sánh {safe_float(valuation.get('relative_value')):,.0f}"),
                unsafe_allow_html=True)
with c4:
    st.markdown(kpi("Chênh lệch định giá", f"{pct(upside):+.1f}%",
                    f"Giá mua hợp lý {safe_float(valuation.get('fair_buy_price')):,.0f}",
                    COLORS["up"] if upside > 0 else COLORS["down"]),
                unsafe_allow_html=True)
with c5:
    st.markdown(kpi("Altman Z-Score", f"{safe_float(risk.get('altman', {}).get('z_score')):.2f}",
                    zone, ZONE_COLORS.get(zone, COLORS["text"])),
                unsafe_allow_html=True)

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

# --- Tabs ---
tabs = st.tabs([
    "Tổng quan", "12 chỉ số", "Cơ bản", "Định giá",
    "Kỹ thuật", "Rủi ro", "Nhật ký đầu tư", "JSON", "💬 Trợ lý AI",
])

# ============================ TAB 1: TỔNG QUAN =============================
with tabs[0]:
    left, right = st.columns([1.55, 1], gap="large")

    with left:
        st.markdown("**Diễn biến giá & khối lượng**")
        st.plotly_chart(candlestick_chart(technical), use_container_width=True)

    with right:
        st.markdown("**Điểm số phân rã 5 trụ cột**")
        render_pillars(score)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        st.markdown("**Dự báo 3 kịch bản giá**")
        st.plotly_chart(scenario_chart(scenarios), use_container_width=True)
        meta = scenarios.get("meta", {})
        st.caption(
            f"{meta.get('model', '')} · chân trời {meta.get('horizon_days', '')} phiên · "
            f"{meta.get('train_samples', 0)} mẫu huấn luyện · "
            f"R² in-sample {meta.get('r2_in_sample', 'n/a')} · "
            f"khoảng tin cậy 95% (±1.96σ, σ = {safe_float(scenarios.get('sigma')):,.0f} VNĐ)"
        )

    st.markdown("---")
    st.markdown("**Luận điểm định lượng**")
    for line in rec.get("rationale", []):
        st.markdown(f"- {line}")

    rr1, rr2, rr3, rr4 = st.columns(4)
    rr1.metric("Giá mục tiêu", f"{safe_float(rec.get('target_price')):,.0f}")
    rr2.metric("Cắt lỗ", f"{safe_float(rec.get('stop_price')):,.0f}")
    rr3.metric("Lợi nhuận/Rủi ro", f"{safe_float(rec.get('risk_reward_ratio')):.2f}x")
    rr4.metric("Tỷ trọng đề xuất", f"{safe_float(rec.get('position_size_pct')):.2f}% NAV")

# ============================ TAB 2: 12 CHỈ SỐ ============================
with tabs[1]:
    st.markdown("**12 chỉ số phân tích tài chính cốt lõi** — sinh tự động từ dữ liệu tính toán")
    render_metrics_12(data.get("metrics_12", []))

# ============================ TAB 3: CƠ BẢN ===============================
with tabs[2]:
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
    c.metric("Dòng tiền tự do", fmt_vnd(f.get("free_cash_flow")))
    d.metric("Tăng trưởng DT (CAGR)", f"{pct(f.get('revenue_cagr')):.2f}%")

    st.markdown("---")
    st.markdown("**Diễn biến kết quả kinh doanh theo quý**")
    st.plotly_chart(financial_history_chart(f.get("history", [])), use_container_width=True)

    with st.expander("Bảng số liệu chi tiết"):
        hist = f.get("history", [])
        if hist:
            df = pd.DataFrame(hist)
            df.columns = ["Kỳ", "Doanh thu", "EBIT", "LNST", "CFO",
                          "Biên LN ròng", "Biên EBIT"]
            st.dataframe(df, use_container_width=True, hide_index=True)

# ============================ TAB 4: ĐỊNH GIÁ =============================
with tabs[3]:
    v = valuation
    a, b, c, d = st.columns(4)
    a.metric("P/E", f"{safe_float(v.get('pe')):.2f}", f"Ngành {safe_float(v.get('peer_pe')):.2f}")
    b.metric("P/B", f"{safe_float(v.get('pb')):.2f}", f"Ngành {safe_float(v.get('peer_pb')):.2f}")
    c.metric("EPS (TTM)", f"{safe_float(v.get('eps')):,.0f}")
    d.metric("Giá trị sổ sách/CP", f"{safe_float(v.get('bvps')):,.0f}")

    a, b, c, d = st.columns(4)
    a.metric("WACC", f"{pct(v.get('wacc')):.2f}%")
    b.metric("Giá trị nội tại (DCF)", f"{safe_float(v.get('intrinsic_value')):,.0f}")
    c.metric("Định giá so sánh", f"{safe_float(v.get('relative_value')):,.0f}")
    d.metric("Vốn hoá", fmt_vnd(v.get("market_cap")))

    st.markdown("---")
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("**Dòng tiền chiết khấu 5 năm**")
        st.plotly_chart(dcf_chart(v.get("dcf", {})), use_container_width=True)
    with col2:
        st.markdown("**Cơ cấu chi phí vốn (WACC)**")
        st.plotly_chart(wacc_chart(v.get("wacc_detail", {})), use_container_width=True)

    dcf = v.get("dcf", {})
    if dcf.get("note"):
        st.info(dcf["note"])
    st.caption(
        f"Giá trị doanh nghiệp {fmt_vnd(dcf.get('enterprise_value'))} · "
        f"Terminal Value {fmt_vnd(dcf.get('terminal_value'))} "
        f"(PV {fmt_vnd(dcf.get('pv_terminal'))}) · "
        f"Nợ thuần {fmt_vnd(v.get('net_debt'))} · "
        f"g dự báo {pct(dcf.get('growth_used')):.2f}%/năm, "
        f"g vĩnh viễn {pct(dcf.get('terminal_growth')):.2f}%"
    )

    with st.expander("Chi tiết tham số WACC"):
        wd = v.get("wacc_detail", {})
        st.dataframe(
            pd.DataFrame([
                {"Tham số": "Lãi suất phi rủi ro (Rf)", "Giá trị": f"{pct(wd.get('risk_free_rate')):.2f}%"},
                {"Tham số": "Phần bù rủi ro (ERP)", "Giá trị": f"{pct(wd.get('equity_risk_premium')):.2f}%"},
                {"Tham số": "Beta sử dụng", "Giá trị": f"{safe_float(wd.get('beta_used')):.3f}"},
                {"Tham số": "Chi phí vốn CSH (Re)", "Giá trị": f"{pct(wd.get('cost_of_equity')):.2f}%"},
                {"Tham số": "Chi phí nợ vay (Rd)", "Giá trị": f"{pct(wd.get('cost_of_debt')):.2f}%"},
                {"Tham số": "Tỷ trọng vốn CSH", "Giá trị": f"{pct(wd.get('weight_equity')):.2f}%"},
                {"Tham số": "Tỷ trọng nợ vay", "Giá trị": f"{pct(wd.get('weight_debt')):.2f}%"},
                {"Tham số": "Thuế suất TNDN", "Giá trị": f"{pct(wd.get('tax_rate')):.2f}%"},
                {"Tham số": "WACC", "Giá trị": f"{pct(v.get('wacc')):.2f}%"},
            ]),
            use_container_width=True, hide_index=True,
        )

# ============================ TAB 5: KỸ THUẬT =============================
with tabs[4]:
    t = technical
    a, b, c, d, e = st.columns(5)
    a.metric("Xu hướng", t.get("trend", ""))
    b.metric("Tín hiệu", t.get("signal", ""))
    c.metric("RSI 14", f"{safe_float(t.get('rsi14')):.2f}")
    d.metric("EMA20", f"{safe_float(t.get('ema20')):,.0f}")
    e.metric("EMA50", f"{safe_float(t.get('ema50')):,.0f}")

    a, b, c, d, e = st.columns(5)
    a.metric("Hỗ trợ (60 phiên)", f"{safe_float(t.get('support')):,.0f}")
    b.metric("Kháng cự (60 phiên)", f"{safe_float(t.get('resistance')):,.0f}")
    c.metric("MACD", f"{safe_float(t.get('macd')):.3f}")
    d.metric("Signal", f"{safe_float(t.get('macd_signal')):.3f}")
    e.metric("KL / TB20 phiên", f"{safe_float(t.get('volume_ratio')):.2f}x")

    st.markdown("---")
    st.plotly_chart(momentum_chart(technical), use_container_width=True)
    st.caption(
        f"Khoảng cách tới hỗ trợ {pct(t.get('distance_to_support')):.2f}% · "
        f"tới kháng cự {pct(t.get('distance_to_resistance')):.2f}%"
    )

# ============================ TAB 6: RỦI RO ===============================
with tabs[5]:
    m = risk.get("market", {})
    z = risk.get("altman", {})

    a, b, c, d = st.columns(4)
    a.metric("Altman Z-Score", f"{safe_float(z.get('z_score')):.3f}", z.get("zone", ""))
    b.metric("Beta (vs VNINDEX)", f"{safe_float(m.get('beta')):.3f}")
    c.metric("Biến động năm", f"{pct(m.get('annual_volatility')):.2f}%")
    d.metric("Sụt giảm tối đa", f"{pct(m.get('max_drawdown')):.2f}%")

    a, b, c, d = st.columns(4)
    a.metric("VaR 95% (ngày)", f"{pct(m.get('var_95_daily')):.2f}%")
    b.metric("Sharpe Ratio", f"{safe_float(m.get('sharpe_ratio')):.3f}")
    c.metric("Tương quan thị trường", f"{safe_float(m.get('correlation_with_index')):.3f}")
    d.metric("Hệ số thanh toán hiện hành", f"{safe_float(risk.get('current_ratio')):.2f}x")

    st.markdown("---")
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("**Cấu phần Altman Z-Score**")
        comp = z.get("components", {})
        names = {
            "X1_working_capital_ratio": "X1 · Vốn lưu động / Tổng TS",
            "X2_retained_earnings_ratio": "X2 · LN giữ lại / Tổng TS",
            "X3_ebit_ratio": "X3 · EBIT / Tổng TS",
            "X4_market_cap_to_liabilities": "X4 · Vốn hoá / Tổng nợ",
            "X5_asset_turnover": "X5 · Doanh thu / Tổng TS",
        }
        weights = {"X1_working_capital_ratio": 1.2, "X2_retained_earnings_ratio": 1.4,
                   "X3_ebit_ratio": 3.3, "X4_market_cap_to_liabilities": 0.6,
                   "X5_asset_turnover": 0.999}
        rows = [
            {"Biến": names[k], "Giá trị": round(safe_float(val), 4),
             "Trọng số": weights[k],
             "Đóng góp": round(safe_float(val) * weights[k], 4)}
            for k, val in comp.items() if k in names
        ]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(z.get("description", ""))

    with col2:
        st.markdown("**Sụt giảm từ đỉnh (Drawdown)**")
        st.plotly_chart(drawdown_chart(technical), use_container_width=True)

    flags = risk.get("risk_flags", [])
    if flags:
        st.markdown("**Cờ cảnh báo rủi ro**")
        for flag in flags:
            st.markdown(
                f'<div style="border-left:3px solid {COLORS["down"]};padding:8px 12px;'
                f'background:{COLORS["panel"]};margin-bottom:6px;font-size:13px">{flag}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("Không phát hiện cờ rủi ro nổi bật theo bộ tiêu chí định lượng.")

# ============================ TAB 7: NHẬT KÝ ==============================
with tabs[6]:
    st.markdown("**Bảng nhật ký đầu tư (Investment Thesis Journal)**")
    j = journal
    st.markdown(
        badge(str(j.get("status", "")),
              ACTION_COLORS.get(action, COLORS["accent"])),
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    journal_rows = [
        ("Mã cổ phiếu", j.get("symbol", "")),
        ("Ngày vào lệnh", j.get("entry_date", "")),
        ("Giá mua (thị giá)", f"{safe_float(j.get('entry_price')):,.0f} VNĐ"),
        ("Luận điểm đầu tư", j.get("thesis", "")),
        ("Catalysts", j.get("catalysts", "")),
        ("Rủi ro (Bear Case)", j.get("bear_risk", "")),
        ("Giá mục tiêu", f"{safe_float(j.get('target_price')):,.0f} VNĐ"),
        ("Ngưỡng cắt lỗ", f"{safe_float(j.get('stop_loss')):,.0f} VNĐ"),
        ("Tỷ trọng danh mục", f"{safe_float(j.get('position_size_pct')):.2f}% NAV"),
        ("Trạng thái vị thế", j.get("status", "")),
    ]
    df_journal = pd.DataFrame({
        "Trường": [r[0] for r in journal_rows],
        "Nội dung": [r[1] for r in journal_rows],
    })
    st.dataframe(df_journal, use_container_width=True, hide_index=True,
                 column_config={"Nội dung": st.column_config.TextColumn(width="large")})

    st.markdown("---")
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("**Ảnh chụp điểm số tại thời điểm ghi nhận**")
        st.plotly_chart(pillar_chart(score), use_container_width=True)
    with col2:
        st.markdown("**Xuất dữ liệu**")
        st.download_button(
            "Tải nhật ký (CSV)",
            df_journal.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"nhat_ky_dau_tu_{symbol}.csv",
            mime="text/csv",
        )
        st.download_button(
            "Tải báo cáo đầy đủ (JSON)",
            json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f"phan_tich_{symbol}.json",
            mime="application/json",
        )
        st.caption(
            "Nhật ký là ảnh chụp tại thời điểm phân tích. Mỗi lần chạy lại, "
            "các mức giá mục tiêu và cắt lỗ được tính lại theo dữ liệu mới nhất."
        )

# ============================ TAB 8: JSON =================================
with tabs[7]:
    st.markdown("**Payload JSON trả về từ Module 6** — chính là dữ liệu mà API Gateway phục vụ")
    st.code(f"GET {api_url}/api/v1/analyze/{symbol}", language="bash")
    st.json(data, expanded=False)

# ============================ TAB 9: TRỢ LÝ AI =============================
with tabs[8]:
    st.markdown(f"**💬 Trợ lý AI Phân tích Đầu tư ({symbol})**")
    st.caption("Trợ lý AI tích hợp dữ liệu định lượng thời gian thực, mô hình định giá DCF và chỉ số tài chính.")

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

        # Hiển thị lịch sử chat
        for role, msg in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(msg)

        # Gợi ý câu hỏi nhanh
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
                with st.spinner("AI đang phân tích dữ liệu..."):
                    reply = bot.ask(user_query, context_data=data)
                st.markdown(reply)
                st.session_state.chat_history.append(("assistant", reply))

            if selected_preset:
                st.rerun()

# --- Chân trang ---
st.markdown(
    f'<div class="footnote">'
    f"Toàn bộ số liệu do hệ thống tự tính từ dữ liệu thô: mô hình DCF/WACC, "
    f"Altman Z-Score, chỉ báo kỹ thuật và Random Forest Regressor. "
    f"Kết quả là đầu ra định lượng phục vụ tham khảo, không phải khuyến nghị "
    f"đầu tư được cấp phép. Người dùng chịu trách nhiệm với quyết định giao dịch "
    f"của mình.</div>",
    unsafe_allow_html=True,
)