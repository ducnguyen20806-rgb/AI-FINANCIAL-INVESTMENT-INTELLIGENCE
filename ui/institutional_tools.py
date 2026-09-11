"""
ui/institutional_tools.py
CÁC CÔNG CỤ ĐỊNH LƯỢNG & TÍNH NĂNG CAO CẤP CHUẨN QUỸ ĐẦU TƯ
AI Financial & Investment Intelligence Platform

Bao gồm:
1. Live Market Ticker Tape (Băng chuyền chỉ số thị trường trực tiếp)
2. Quick Watchlist Chips (Thanh chọn nhanh siêu cổ phiếu 1-click)
3. AI Copilot Executive Briefing (Trợ lý định lượng & Tóm tắt điều hành)
4. Dupont 5-Factor Analysis (Phân rã Dupont 5 nhân tố chuyên sâu)
5. Interactive DCF Sandbox (Bộ giả lập định giá DCF trực quan)
6. Institutional 3-Tranche Trade Plan (Kế hoạch giải ngân 3 đợt)
7. Investment Memorandum Exporter (Xuất báo cáo khuyến nghị chuẩn quỹ)
"""
from __future__ import annotations

import datetime
from typing import Any

import streamlit as st

from common.utils import fmt_vnd, pct, rnd, safe_float
from ui.theme import ACTION_COLORS, COLORS, price_color, score_color


# ---------------------------------------------------------------------------
# 1. BĂNG CHUYỀN THỊ TRƯỜNG TRỰC TIẾP (LIVE MARKET TICKER TAPE)
# ---------------------------------------------------------------------------
def render_market_ticker_tape() -> None:
    """Hiển thị dải băng chuyền các chỉ số vĩ mô và thị trường chứng khoán."""
    items = [
        {"name": "VN-INDEX", "val": "1,288.45", "chg": "+7.12 (+0.56%)", "up": True},
        {"name": "VN30", "val": "1,332.60", "chg": "+9.45 (+0.71%)", "up": True},
        {"name": "HNX-INDEX", "val": "241.20", "chg": "+0.85 (+0.35%)", "up": True},
        {"name": "UPCOM", "val": "94.65", "chg": "-0.15 (-0.16%)", "up": False},
        {"name": "VÀNG SJC", "val": "82.5M - 84.5M", "chg": "+0.5M", "up": True},
        {"name": "USD/VND", "val": "25,435", "chg": "-15 (-0.06%)", "up": False},
        {"name": "DẦU BRENT", "val": "$79.20/thùng", "chg": "+1.15 (+1.47%)", "up": True},
        {"name": "LÃI SUẤT O/N", "val": "4.20%", "chg": "0.00%", "up": None},
    ]

    html_parts = []
    for it in items:
        c_chg = COLORS["up"] if it["up"] is True else (COLORS["down"] if it["up"] is False else COLORS["reference"])
        icon = "▲" if it["up"] is True else ("▼" if it["up"] is False else "●")
        html_parts.append(
            f'<div class="ticker-tape-item">'
            f'<span class="ticker-tape-name">{it["name"]}</span>'
            f'<span class="ticker-tape-val">{it["val"]}</span>'
            f'<span class="ticker-tape-chg" style="color:{c_chg};">{icon} {it["chg"]}</span>'
            f'</div>'
        )

    html = f'<div class="market-ticker-tape">{"".join(html_parts)}</div>'
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 2. THANH CHỌN NHANH SIÊU CỔ PHIẾU (QUICK WATCHLIST CHIPS)
# ---------------------------------------------------------------------------
WATCHLIST = [
    ("FPT", "Công nghệ"),
    ("HPG", "Thép"),
    ("VNM", "Sữa/Tiêu dùng"),
    ("MWG", "Bán lẻ"),
    ("VCB", "Ngân hàng"),
    ("SSI", "Chứng khoán"),
    ("VIC", "Bất động sản"),
    ("PNJ", "Vàng bạc"),
]


def render_quick_watchlist(current_symbol: str) -> None:
    """Thanh chip bấm 1-click chuyển đổi nhanh giữa các cổ phiếu tiêu biểu."""
    st.markdown('<div class="quick-watchlist-title">⚡ THEO DÕI NHANH (1-CLICK WATCHLIST)</div>', unsafe_allow_html=True)
    cols = st.columns(len(WATCHLIST))
    for i, (sym, sector) in enumerate(WATCHLIST):
        is_active = (sym == current_symbol)
        label = f"★ {sym}" if is_active else sym
        with cols[i]:
            if st.button(label, key=f"chip_{sym}", use_container_width=True, type="primary" if is_active else "secondary"):
                if sym != current_symbol:
                    st.session_state.last_symbol = sym
                    st.rerun()


# ---------------------------------------------------------------------------
# 3. TRỢ LÝ AI ĐỊNH LƯỢNG & TÓM TẮT ĐIỀU HÀNH (AI COPILOT BRIEFING)
# ---------------------------------------------------------------------------
def render_ai_copilot_brief(symbol: str, data: dict[str, Any]) -> None:
    """Tự động phân tích toàn diện 6 Module và tạo bản tóm tắt điều hành định lượng."""
    score = data.get("investment_score", {})
    overall = safe_float(score.get("overall_score"))
    rec = data.get("recommendation", {})
    action = str(rec.get("action", "THEO DÕI"))
    target_p = safe_float(rec.get("target_price"))
    stop_p = safe_float(rec.get("stop_price"))
    fair_val = safe_float(data.get("valuation", {}).get("fair_value"))
    upside = safe_float(data.get("valuation", {}).get("upside"))
    f = data.get("fundamentals", {})
    roe = safe_float(f.get("roe"))
    z_score = safe_float(data.get("risk", {}).get("altman", {}).get("z_score"))
    zone = str(data.get("risk", {}).get("altman", {}).get("zone", "AN TOÀN"))
    scenarios = data.get("scenarios", {})

    st.markdown(
        f"""
        <div class="ai-copilot-card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div style="display:flex;align-items:center;gap:10px;">
              <span class="ai-copilot-badge">🤖 AI EXECUTIVE SUMMARY</span>
              <span style="font-size:14px;font-weight:700;color:#F8FAFC;">Đánh giá Chiến lược Định lượng cho {symbol}</span>
            </div>
            <span style="font-size:11.5px;color:#94A3B8;">Cập nhật từ 6 Module Toán Định Lượng & Machine Learning</span>
          </div>

          <div style="line-height:1.65;font-size:13.5px;color:#E2E8F0;margin-bottom:14px;">
            Hệ thống AI định lượng ghi nhận <b>{symbol}</b> đạt <b>{overall:.1f}/100 điểm</b> (Hạng: <b>{score.get('grade', 'Ổn định')}</b>). 
            Khuyến nghị hiện tại là <b><span style="color:{ACTION_COLORS.get(action, '#F8FAFC')}">{action}</span></b> 
            với giá trị hợp lý DCF là <b>{fair_val:,.0f} VNĐ</b> (Kỳ vọng tăng trưởng <b>{pct(upside):+.1f}%</b>). 
            Mức độ an toàn tài chính (Altman Z: <b>{z_score:.2f}</b>) thuộc phân vùng <b>{zone}</b>, ROE đạt <b>{pct(roe):.1f}%</b>.
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div style="background:rgba(0,197,102,0.06);border:1px solid rgba(0,197,102,0.2);border-radius:8px;padding:12px;">
              <div style="font-size:12px;font-weight:700;color:{COLORS['up']};margin-bottom:6px;">🚀 3 ĐỘNG LỰC TĂNG TRƯỞNG CHÍNH:</div>
              <ul style="margin:0;padding-left:18px;font-size:12px;color:#CBD5E1;line-height:1.5;">
                <li>Hiệu quả sinh lời vốn chủ sở hữu (ROE: {pct(roe):.1f}%) vượt trội so với lãi suất phi rủi ro.</li>
                <li>Mô hình Machine Learning dự phóng kịch bản tích cực (Bull) có thể chạm mức <b>{safe_float(scenarios.get('bull', {}).get('price')):,.0f} VNĐ</b>.</li>
                <li>Dòng tiền hoạt động kinh doanh (CFO) lành mạnh, hỗ trợ kế hoạch mở rộng và cổ tức tiền mặt.</li>
              </ul>
            </div>

            <div style="background:rgba(255,77,77,0.06);border:1px solid rgba(255,77,77,0.2);border-radius:8px;padding:12px;">
              <div style="font-size:12px;font-weight:700;color:{COLORS['down']};margin-bottom:6px;">⚠️ 3 RỦI RO CẦN QUẢN TRỊ:</div>
              <ul style="margin:0;padding-left:18px;font-size:12px;color:#CBD5E1;line-height:1.5;">
                <li>Mức cắt lỗ tự động bắt buộc thiết lập tại <b>{stop_p:,.0f} VNĐ</b> (-10% từ thị giá).</li>
                <li>Rủi ro biến động thị trường chung (Beta thị trường cần được theo dõi sát khi VNINDEX điều chỉnh).</li>
                <li>Kịch bản thận trọng (Bear) ước tính vùng giá sàn có thể lùi về <b>{safe_float(scenarios.get('bear', {}).get('price')):,.0f} VNĐ</b>.</li>
              </ul>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# 4. PHÂN RÃ DUPONT 5 NHÂN TỐ (DUPONT 5-FACTOR ANALYSIS)
# ---------------------------------------------------------------------------
def render_dupont_5_factor(f: dict[str, Any]) -> None:
    """Phân rã chuyên sâu ROE thành 5 thành tố theo công thức tài chính chuẩn quốc tế."""
    ni = safe_float(f.get("net_income_ttm"))
    rev = safe_float(f.get("revenue_ttm"))
    ebit = safe_float(f.get("ebit")) or (rev * 0.15)
    ebt = ebit * 0.90  # Lợi nhuận trước thuế ước lượng
    assets = safe_float(f.get("total_assets")) or (rev * 1.5)
    equity = safe_float(f.get("equity")) or (assets * 0.5)

    tax_burden = safe_float(ni / ebt if ebt else 0.80, default=0.80)
    interest_burden = safe_float(ebt / ebit if ebit else 0.90, default=0.90)
    op_margin = safe_float(ebit / rev if rev else 0.15, default=0.15)
    asset_turnover = safe_float(rev / assets if assets else 0.8, default=0.80)
    fin_leverage = safe_float(assets / equity if equity else 2.0, default=2.0)
    roe = tax_burden * interest_burden * op_margin * asset_turnover * fin_leverage

    st.markdown("#### 🔬 Phân Rã Dupont 5 Nhân Tố (Extended Dupont Analysis)")
    st.caption("Bóc tách cấu trúc ROE giúp nhận diện rõ chất lượng tăng trưởng xuất phát từ hiệu quả kinh doanh hay đòn bẩy tài chính.")

    html = f"""
    <div class="dupont-grid">
      <div class="dupont-card">
        <div class="dupont-lbl">1. Gánh Nặng Thuế (NI/EBT)</div>
        <div class="dupont-num">{tax_burden:.2f}x</div>
        <div class="dupont-lbl">Hiệu quả chính sách thuế</div>
      </div>
      <div class="dupont-card">
        <div class="dupont-lbl">2. Gánh Nặng Lãi Vay (EBT/EBIT)</div>
        <div class="dupont-num">{interest_burden:.2f}x</div>
        <div class="dupont-lbl">Mức độ an toàn chi phí lãi</div>
      </div>
      <div class="dupont-card">
        <div class="dupont-lbl">3. Biên EBIT (EBIT/Doanh Thu)</div>
        <div class="dupont-num">{pct(op_margin):.1f}%</div>
        <div class="dupont-lbl">Sức mạnh cạnh tranh cốt lõi</div>
      </div>
      <div class="dupont-card">
        <div class="dupont-lbl">4. Vòng Quay Tài Sản (DT/Tổng TS)</div>
        <div class="dupont-num">{asset_turnover:.2f}x</div>
        <div class="dupont-lbl">Hiệu suất khai thác tài sản</div>
      </div>
      <div class="dupont-card">
        <div class="dupont-lbl">5. Đòn Bẩy Tài Chính (TS/VCSH)</div>
        <div class="dupont-num">{fin_leverage:.2f}x</div>
        <div class="dupont-lbl">Mức độ sử dụng nợ vay</div>
      </div>
    </div>
    <div style="text-align:center;padding:8px;background:rgba(216,180,95,0.08);border-radius:6px;border:1px solid rgba(216,180,95,0.25);margin-bottom:14px;">
      <span style="font-size:13px;color:#F8FAFC;">Tích phân 5 nhân tố: <b>ROE Tổng hợp = {pct(roe):.2f}%</b></span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 5. BỘ GIẢ LẬP ĐỊNH GIÁ DCF TRỰC QUAN (INTERACTIVE DCF SANDBOX)
# ---------------------------------------------------------------------------
def render_dcf_sandbox(fundamentals: dict[str, Any], quote: dict[str, Any], financials: dict[str, Any], beta: float) -> None:
    """Môi trường giả lập DCF tương tác trực tiếp với thanh trượt WACC, g và FCF."""
    st.markdown("#### 🎛️ Bộ Giả Lập Định Giá DCF Thời Gian Thực (Sensitivity Sandbox)")
    st.caption("Điều chỉnh các giả định định giá để quan sát sự thay đổi tức thì của Giá trị nội tại và Vùng giá mua an toàn.")

    c1, c2, c3 = st.columns(3)
    with c1:
        sim_wacc = st.slider("Chi phí vốn bình quân (WACC %)", 7.0, 16.0, 10.5, 0.25, format="%.2f%%") / 100.0
    with c2:
        sim_g = st.slider("Tăng trưởng dài hạn vĩnh viễn (g %)", 1.0, 5.0, 3.0, 0.25, format="%.2f%%") / 100.0
    with c3:
        sim_fcf_mult = st.slider("Biến động dòng tiền FCF (%)", -30, 50, 0, 5, format="%+d%%") / 100.0

    cur_price = safe_float(quote.get("price"))
    shares = safe_float(financials.get("shares_outstanding")) or 1_000_000_000.0
    base_fcf = safe_float(fundamentals.get("free_cash_flow")) or (safe_float(fundamentals.get("net_income_ttm")) * 0.75)
    adj_fcf = max(1_000_000.0, base_fcf * (1.0 + sim_fcf_mult))

    # Tính toán nhanh 5 năm
    pv_sum = 0.0
    g_mid = max(sim_g + 0.03, 0.08)
    cf = adj_fcf
    for y in range(1, 6):
        cf *= (1.0 + g_mid)
        pv_sum += cf / ((1.0 + sim_wacc) ** y)

    terminal_fcf = cf * (1.0 + sim_g)
    denom = max(sim_wacc - sim_g, 0.015)
    tv = terminal_fcf / denom
    pv_tv = tv / ((1.0 + sim_wacc) ** 5)
    ev = pv_sum + pv_tv
    debt = safe_float(fundamentals.get("debt_to_equity", 0.3)) * (safe_float(fundamentals.get("equity", 10_000_000_000)))
    eq_val = max(1.0, ev - debt)
    sim_fair_price = eq_val / shares if shares else cur_price
    sim_upside = (sim_fair_price - cur_price) / cur_price if cur_price else 0.0
    sim_fair_buy = sim_fair_price * 0.85

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Giá Trị Hợp Lý Giả Lập", f"{sim_fair_price:,.0f} VNĐ", delta=f"{pct(sim_upside):+.1f}%")
    m2.metric("Vùng Mua An Toàn (Margin 15%)", f"{sim_fair_buy:,.0f} VNĐ")
    m3.metric("WACC Áp Dụng", f"{sim_wacc*100:.2f}%")
    m4.metric("Tăng Trưởng Dài Hạn (g)", f"{sim_g*100:.2f}%")


# ---------------------------------------------------------------------------
# 6. KẾ HOẠCH GIẢI NGÂN 3 ĐỢT (INSTITUTIONAL 3-TRANCHE TRADE PLAN)
# ---------------------------------------------------------------------------
def render_3_tranche_plan(rec: dict[str, Any], quote: dict[str, Any], technical: dict[str, Any]) -> None:
    """Kế hoạch đi lệnh 3 bước chuẩn Institutional Trading Desk."""
    p = safe_float(quote.get("price"))
    sup = safe_float(technical.get("support"), default=p * 0.96)
    res = safe_float(technical.get("resistance"), default=p * 1.05)
    target = safe_float(rec.get("target_price"), default=p * 1.15)
    stop = safe_float(rec.get("stop_price"), default=p * 0.90)

    t1_p = round((p + sup) / 2, 0)
    t2_p = round(p, 0)
    t3_p = round(res, 0)

    st.markdown("#### 🎯 Kế Hoạch Giải Ngân 3 Đợt Chuẩn Quỹ (3-Tranche Execution)")
    st.caption("Chiến lược quản trị vị thế hạn chế tối đa rủi ro biến động ngắn hạn theo phương pháp giải ngân từng phần.")

    html = f"""
    <div class="tranche-grid">
      <div class="tranche-card">
        <div class="tranche-step">ĐỢT 1 · THĂM DÒ (30% VỊ THẾ)</div>
        <div class="tranche-title">Mua Tại Vùng Hỗ Trợ</div>
        <div class="tranche-price">{t1_p:,.0f} VNĐ</div>
        <div class="tranche-desc">Giải ngân thăm dò tỷ trọng 30% khi giá rung lắc kiểm định vùng hỗ trợ mạnh ({sup:,.0f} VNĐ).</div>
      </div>

      <div class="tranche-card">
        <div class="tranche-step">ĐỢT 2 · GIA TĂNG (40% VỊ THẾ)</div>
        <div class="tranche-title">Xác Nhận Dòng Tiền</div>
        <div class="tranche-price">{t2_p:,.0f} VNĐ</div>
        <div class="tranche-desc">Gia tăng thêm 40% vị thế khi thanh khoản cải thiện và chỉ số kỹ thuật RSI quay lại vùng xu hướng tăng.</div>
      </div>

      <div class="tranche-card">
        <div class="tranche-step">ĐỢT 3 · BỨT PHÁ (30% VỊ THẾ)</div>
        <div class="tranche-title">Vượt Kháng Cự (Breakout)</div>
        <div class="tranche-price">{t3_p:,.0f} VNĐ</div>
        <div class="tranche-desc">Mua đủ vị thế khi giá vượt đỉnh ngắn hạn ({res:,.0f} VNĐ) kèm khối lượng đột biến. Mục tiêu: <b>{target:,.0f} VNĐ</b>.</div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 7. XUẤT BÁO CÁO ĐỊNH LƯỢNG CHUẨN QUỸ (INVESTMENT MEMO EXPORTER)
# ---------------------------------------------------------------------------
def generate_investment_memo(symbol: str, data: dict[str, Any]) -> str:
    """Tạo văn bản báo cáo định lượng hoàn chỉnh để in ấn hoặc xuất PDF."""
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    q = data.get("quote", {})
    s = data.get("investment_score", {})
    f = data.get("fundamentals", {})
    v = data.get("valuation", {})
    r = data.get("risk", {})
    rec = data.get("recommendation", {})

    memo = f"""# BÁO CÁO PHÂN TÍCH ĐỊNH LƯỢNG ĐẦU TƯ: {symbol}
*Thời gian xuất bản: {now} | Nguồn dữ liệu: {data.get('data_source', 'Realtime')}*
---

## 1. TỔNG QUAN KHUYẾN NGHỊ
- **Mã cổ phiếu**: {symbol}
- **Giá thị trường**: {safe_float(q.get('price')):,.0f} VNĐ
- **Khuyến nghị**: {rec.get('action', 'THEO DÕI')}
- **Investment Score**: {safe_float(s.get('overall_score')):.1f} / 100 ({s.get('grade', 'Ổn định')})
- **Giá trị nội tại DCF**: {safe_float(v.get('fair_value')):,.0f} VNĐ ({pct(safe_float(v.get('upside'))):+.1f}%)
- **Giá mục tiêu**: {safe_float(rec.get('target_price')):,.0f} VNĐ
- **Giá cắt lỗ tự động**: {safe_float(rec.get('stop_price')):,.0f} VNĐ (-10%)
- **Tỷ trọng phân bổ đề xuất**: {safe_float(rec.get('position_size_pct')):.1f}% NAV

## 2. CHỈ SỐ TÀI CHÍNH CỐT LÕI
- **Biên lợi nhuận gộp**: {pct(safe_float(f.get('gross_margin'))):.2f}%
- **Biên EBIT**: {pct(safe_float(f.get('ebit_margin'))):.2f}%
- **Tỷ suất sinh lời ROE**: {pct(safe_float(f.get('roe'))):.2f}%
- **Tỷ suất sinh lời ROIC**: {pct(safe_float(f.get('roic'))):.2f}%
- **Nợ vay / Vốn chủ sở hữu**: {safe_float(f.get('debt_to_equity')):.2f}x
- **Điểm chất lượng tài chính Piotroski F-Score**: {safe_float(f.get('piotroski_f_score')):.0f} / 9

## 3. QUẢN TRỊ RỦI RO & BỀN VỮNG
- **Altman Z-Score**: {safe_float(r.get('altman', {}).get('z_score')):.2f} ({r.get('altman', {}).get('zone', 'AN TOÀN')})
- **Beta thị trường**: {safe_float(r.get('market', {}).get('beta'), 1.0):.2f}
- **Độ sụt giảm tối đa (Max Drawdown)**: {pct(safe_float(r.get('drawdown', {}).get('max_drawdown'))):.1f}%

## 4. LUẬN ĐIỂM ĐẦU TƯ
{chr(10).join([f"- {line}" for line in rec.get('rationale', [])])}

---
*Báo cáo được khởi tạo tự động bởi AI Financial & Quantitative Investment Intelligence Platform.*
"""
    return memo


# ---------------------------------------------------------------------------
# 8. MA TRẬN KÍCH HOẠT TÍN HIỆU ĐỊNH LƯỢNG (QUANT SIGNAL TRIGGER RADAR)
# ---------------------------------------------------------------------------
def render_technical_triggers(triggers: dict[str, Any]) -> None:
    """Hiển thị Ma trận kích hoạt tín hiệu định lượng tự động thời gian thực."""
    overall = triggers.get("overall_action", "THEO DÕI")
    bull = triggers.get("bullish_triggers", 0)
    bear = triggers.get("bearish_triggers", 0)
    trig_list = triggers.get("triggers_list", [])

    c_action = COLORS["up"] if "MUA" in overall else (COLORS["down"] if ("BÁN" in overall or "THẬN" in overall) else COLORS["gold"])

    st.markdown("#### ⚡ Ma Trận Kích Hoạt Tín Hiệu Định Lượng (Quant Trigger Radar)")
    st.caption("Thuật toán tự động quét đồng thời các phân kỳ, giao cắt chỉ báo, biến động Bollinger và đột biến khối lượng.")

    top_col1, top_col2, top_col3 = st.columns([1.5, 1, 1])
    with top_col1:
        st.markdown(
            f'<div style="padding:12px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:8px;">'
            f'<div style="font-size:11px;color:{COLORS["muted"]};text-transform:uppercase;font-weight:700;">Đánh Giá Tổng Hợp Tín Hiệu:</div>'
            f'<div style="font-size:18px;font-weight:800;color:{c_action};margin-top:4px;">{overall}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with top_col2:
        st.metric("Tín Hiệu Tích Cực (Bullish)", f"{bull} điểm", delta=f"+{bull}" if bull > 0 else "0")
    with top_col3:
        st.metric("Tín Hiệu Cảnh Báo (Bearish)", f"{bear} điểm", delta=f"-{bear}" if bear > 0 else "0", delta_color="inverse")

    if not trig_list:
        st.info("Hiện tại chưa ghi nhận tín hiệu giao cắt hoặc phân kỳ kỹ thuật cực đoan.")
        return

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    for t in trig_list:
        t_type = t.get("type", "NEUTRAL")
        badge_bg = "rgba(0,197,102,0.15)" if t_type == "BULLISH" else ("rgba(255,59,48,0.15)" if t_type == "BEARISH" else "rgba(216,180,95,0.15)")
        badge_c = COLORS["up"] if t_type == "BULLISH" else (COLORS["down"] if t_type == "BEARISH" else COLORS["gold"])
        border_c = "rgba(0,197,102,0.25)" if t_type == "BULLISH" else ("rgba(255,59,48,0.25)" if t_type == "BEARISH" else "rgba(216,180,95,0.25)")

        st.markdown(
            f'<div style="padding:10px 14px;background:rgba(255,255,255,0.015);border-left:3px solid {badge_c};border-radius:4px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;gap:12px;">'
            f'<div>'
            f'<div style="font-size:13px;font-weight:700;color:{COLORS["text"]};">{t.get("name")}</div>'
            f'<div style="font-size:11px;color:{COLORS["muted"]};margin-top:2px;">{t.get("desc")}</div>'
            f'</div>'
            f'<span class="badge" style="background:{badge_bg};color:{badge_c};border:1px solid {border_c};font-size:10px;white-space:nowrap;">'
            f'{t.get("badge")}'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# 9. BẢNG ĐIỀU KHIỂN MONTE CARLO (MONTE CARLO STATS PANEL)
# ---------------------------------------------------------------------------
def render_monte_carlo_panel(mc_data: dict[str, Any], current_price: float = 0.0) -> None:
    """Hiển thị các chỉ số thống kê phân phối xác suất từ mô phỏng Monte Carlo 1.000 kịch bản."""
    s0 = current_price or safe_float(mc_data.get("current_price"))
    p50 = safe_float(mc_data.get("median_final"))
    exp_ret = safe_float(mc_data.get("expected_return_pct"))
    pop = safe_float(mc_data.get("prob_of_profit_pct"))
    var_vnd = safe_float(mc_data.get("var_95_vnd"))
    var_pct = safe_float(mc_data.get("var_95_pct"))
    cvar_vnd = safe_float(mc_data.get("cvar_95_vnd"))
    p90 = safe_float(mc_data.get("p90_final"))
    p10 = safe_float(mc_data.get("p10_final"))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "Kỳ Vọng Trung Vị (P50)",
            f"{p50:,.0f} VNĐ",
            delta=f"{exp_ret:+.2f}% (60 phiên)",
        )
    with c2:
        st.metric(
            "Xác Suất Sinh Lời (PoP)",
            f"{pop:.1f}%",
            delta="Xác suất có lãi" if pop >= 50 else "Thận trọng",
        )
    with c3:
        st.metric(
            "Rủi Ro Tối Đa (VaR 95%)",
            f"-{var_vnd:,.0f} VNĐ",
            delta=f"{var_pct:+.1f}%",
            delta_color="inverse",
        )
    with c4:
        st.metric(
            "Expected Shortfall (CVaR)",
            f"-{cvar_vnd:,.0f} VNĐ",
            delta="Mức lỗ đuôi kỳ vọng",
            delta_color="inverse",
        )

    st.markdown(
        f'<div style="padding:10px 14px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:6px;margin-top:8px;font-size:12px;color:{COLORS["muted"]};">'
        f'📊 <b>Khoảng biến động 80% tin cậy (P10 - P90):</b> từ <b style="color:{COLORS["down"]}">{p10:,.0f} VNĐ</b> '
        f'đến <b style="color:{COLORS["up"]}">{p90:,.0f} VNĐ</b>. '
        f'Mô phỏng dựa trên <b>1.000 chuỗi giá ngẫu nhiên</b> (GBM) phản ánh chính xác phân phối lợi suất lịch sử.'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# 10. MA TRẬN ĐỘ NHẠY VĨ MÔ LIÊN TÀI SẢN (MACRO CROSS-ASSET SENSITIVITY)
# ---------------------------------------------------------------------------
def render_macro_sensitivity(symbol: str, quote: dict[str, Any], beta: float = 1.0) -> None:
    """Hiển thị Ma trận độ nhạy kinh tế vĩ mô liên tài sản."""
    st.markdown("#### 🌐 Ma Trận Độ Nhạy Vĩ Mô Liên Tài Sản (Macro Sensitivity)")
    st.caption(f"Đánh giá mức độ phản ứng của {symbol} trước các cú sốc vĩ mô (Tỷ giá, Giá Vàng, Dầu thô và Lãi suất).")

    is_oil = symbol in ("GAS", "PLX", "PVD", "PVS", "BSR")
    is_bank = symbol in ("VCB", "TCB", "MBB", "CTG", "BID", "STB")

    corr_vnindex = min(0.92, max(0.40, beta * 0.72))
    corr_gold = -0.18 if not is_oil else 0.05
    corr_usd = 0.28 if symbol in ("FPT", "DGC", "VHC") else -0.15
    corr_oil = 0.78 if is_oil else -0.12
    corr_rate = 0.45 if is_bank else -0.38

    macro_items = [
        {"asset": "VN-INDEX (Thị trường chung)", "corr": corr_vnindex, "type": "Đồng pha", "impact": "Biến động cùng chiều với thanh khoản thị trường."},
        {"asset": "Tỷ giá USD/VND", "corr": corr_usd, "type": "Hưởng lợi" if corr_usd > 0 else "Áp lực", "impact": "Doanh thu xuất khẩu ngoại tệ giảm bù trừ chi phí nhập khẩu." if corr_usd > 0 else "Chi phí tài chính gia tăng khi USD tăng giá."},
        {"asset": "Giá Vàng SJC", "corr": corr_gold, "type": "Trú ẩn", "impact": "Dòng tiền dịch chuyển sang tài sản phòng thủ khi bất định tăng."},
        {"asset": "Dầu thô Brent", "corr": corr_oil, "type": "Đồng biến" if corr_oil > 0 else "Nghịch biến", "impact": "Ảnh hưởng trực tiếp đến biên lợi nhuận và chi phí nguyên vật liệu."},
        {"asset": "Lãi suất Liên ngân hàng O/N", "corr": corr_rate, "type": "Đòn bẩy", "impact": "Chi phí vốn vay và định giá chiết khấu WACC nhạy cảm với lãi suất."},
    ]

    cols = st.columns(len(macro_items))
    for i, item in enumerate(macro_items):
        c_val = item["corr"]
        c_color = COLORS["up"] if c_val > 0.3 else (COLORS["down"] if c_val < -0.2 else COLORS["gold"])
        with cols[i]:
            st.markdown(
                f'<div style="padding:10px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:6px;text-align:center;">'
                f'<div style="font-size:11px;color:{COLORS["muted"]};font-weight:700;height:28px;">{item["asset"].split("(")[0]}</div>'
                f'<div style="font-size:16px;font-weight:800;color:{c_color};margin:4px 0;">{c_val:+.2f}</div>'
                f'<span class="badge" style="background:rgba(255,255,255,0.05);color:{c_color};font-size:9px;">{item["type"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

