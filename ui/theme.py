"""
ui/theme.py
Hệ thống thị giác & Thiết kế giao diện cao cấp — AI Financial Platform

Bảng màu:
- Tông nền: Navy Dark / Deep Slate (#0B0F17, #0F172A)
- Thẻ chứa dữ liệu: Hiệu ứng kính mờ (Glassmorphism) rgba(30, 41, 59, 0.70) với backdrop blur
- Viền nét: 1px solid rgba(255, 255, 255, 0.08)
- Nút nhấn: Tông Slate tinh tế (#1E293B) và Vàng kim (#D8B45F), loại bỏ xanh dương chói gắt
- Màu chuẩn bảng giá chứng khoán Việt Nam (HOSE/HNX):
    Tím (Trần: #B44BFF), Xanh lá (Tăng: #00C566), Vàng (Tham chiếu: #F5C518),
    Đỏ (Giảm: #FF4D4D), Xanh lơ (Sàn: #00C2D1)
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Bảng màu
# ---------------------------------------------------------------------------
COLORS = {
    "ink": "#0B0F17",           # Nền Slate/Navy sẫm
    "panel": "rgba(30, 41, 59, 0.70)", # Thẻ kính mờ Glassmorphism
    "panel_solid": "#1E293B",   # Nền khối đặc
    "panel_alt": "#0F172A",     # Nền phụ
    "line": "rgba(255, 255, 255, 0.08)", # Đường phân cách viền mỏng
    "text": "#F8FAFC",          # Chữ sáng Slate
    "text_sub": "#CBD5E1",      # Chữ phụ
    "muted": "#94A3B8",         # Chữ mờ / chú thích
    "ceiling": "#B44BFF",       # Giá trần (Tím)
    "up": "#00C566",            # Tăng giá (Xanh lá)
    "reference": "#F5C518",     # Tham chiếu (Vàng)
    "down": "#FF4D4D",          # Giảm giá (Đỏ)
    "floor": "#00C2D1",         # Giá sàn (Xanh lơ)
    "accent": "#38BDF8",        # Điểm nhấn Sky Blue
    "gold": "#D8B45F",          # Điểm nhấn Vàng Kim
    "gold_hover": "#E6C877",    # Vàng kim hover
}

# Màu theo trạng thái nghiệp vụ
ZONE_COLORS = {
    "AN TOÀN": COLORS["up"],
    "CẢNH BÁO": COLORS["reference"],
    "RỦI RO CAO": COLORS["down"],
    "KHÔNG XÁC ĐỊNH": COLORS["muted"],
}

ACTION_COLORS = {
    "MUA": COLORS["ceiling"],
    "TÍCH LUỸ": COLORS["up"],
    "NẮM GIỮ / THEO DÕI": COLORS["reference"],
    "GIẢM TỶ TRỌNG": COLORS["down"],
    "BÁN / TRÁNH": COLORS["down"],
}

PILLAR_LABELS = {
    "fundamental": "Cơ bản",
    "valuation": "Định giá",
    "risk": "Rủi ro",
    "quality": "Chất lượng",
    "momentum": "Động lượng",
}


def price_color(price: float, ref: float, ceiling: float, floor: float) -> str:
    """Trả về mã màu của một mức giá theo đúng quy ước bảng điện HOSE."""
    if ceiling and abs(price - ceiling) < 1e-6:
        return COLORS["ceiling"]
    if floor and abs(price - floor) < 1e-6:
        return COLORS["floor"]
    if not ref:
        return COLORS["reference"]
    if price > ref:
        return COLORS["up"]
    if price < ref:
        return COLORS["down"]
    return COLORS["reference"]


def score_color(score: float) -> str:
    """Màu sắc theo điểm số Investment Score."""
    if score >= 70:
        return COLORS["up"]
    if score >= 50:
        return COLORS["reference"]
    if score >= 35:
        return "#FB923C"
    return COLORS["down"]


# ---------------------------------------------------------------------------
# CSS HỆ THỐNG GIAO DIỆN (GLASSMORPHISM & NAVY THEME)
# ---------------------------------------------------------------------------
def build_css() -> str:
    c = COLORS
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {{
  --ink: {c['ink']};
  --panel: {c['panel']};
  --panel-solid: {c['panel_solid']};
  --line: {c['line']};
  --text: {c['text']};
  --muted: {c['muted']};
  --up: {c['up']};
  --down: {c['down']};
  --ref: {c['reference']};
  --ceiling: {c['ceiling']};
  --floor: {c['floor']};
  --accent: {c['accent']};
  --gold: {c['gold']};
}}

/* Ẩn hoàn toàn thanh Header mặc định của Streamlit (bỏ chữ Deploy và khoảng đen trên cùng) */
header[data-testid="stHeader"] {{
  display: none !important;
}}
#MainMenu, footer {{
  visibility: hidden !important;
  display: none !important;
}}

/* Toàn bộ Canvas chính */
.stApp {{
  background: {c['ink']} !important;
  color: {c['text']} !important;
  font-family: 'Be Vietnam Pro', 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
}}

/* Bố cục Grid & loại bỏ lề đen thừa */
.block-container {{
  padding-top: 0.75rem !important;
  padding-bottom: 2rem !important;
  padding-left: 1.75rem !important;
  padding-right: 1.75rem !important;
  max-width: 100% !important;
}}

/* Thanh Sidebar bên trái thu nhỏ đúng 240px */
section[data-testid="stSidebar"] {{
  width: 240px !important;
  min-width: 240px !important;
  max-width: 240px !important;
  background: #0B0F17 !important;
  border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}}
section[data-testid="stSidebar"] > div {{
  width: 240px !important;
  padding: 1.25rem 0.9rem !important;
}}

/* Typography */
h1, h2, h3, h4 {{
  font-family: 'Plus Jakarta Sans', 'Be Vietnam Pro', sans-serif !important;
  letter-spacing: -0.02em;
  color: {c['text']};
}}

/* ---------- THANH ĐIỀU HƯỚNG CỐ ĐỊNH TRÊN CÙNG (TOP NAVIGATION BAR) ---------- */
.top-navbar {{
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px 18px;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
}}

.nav-brand {{
  display: flex;
  align-items: center;
  gap: 10px;
}}
.nav-logo {{
  font-size: 20px;
  filter: drop-shadow(0 0 8px rgba(216, 180, 95, 0.6));
}}
.nav-title {{
  font-size: 14.5px;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: {c['text']};
}}
.nav-subtitle {{
  font-size: 10.5px;
  color: {c['muted']};
  letter-spacing: 0.02em;
}}

.nav-user-badge {{
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 6px 12px;
}}

/* ---------- THẺ HEADER CÔNG TY (DISPLAY FONT) ---------- */
.company-header {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 4px 0 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 14px;
}}
.company-title-wrap {{
  display: flex;
  align-items: baseline;
  gap: 14px;
}}
.company-symbol-display {{
  font-family: 'Plus Jakarta Sans', 'Be Vietnam Pro', sans-serif;
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1;
  color: #FFFFFF;
}}
.company-fullname {{
  font-size: 15px;
  font-weight: 600;
  color: #CBD5E1;
}}
.company-sector {{
  font-size: 12px;
  color: {c['muted']};
}}

/* ---------- DẢI TICKER STRIP LIỀN MẠCH ---------- */
.ticker-strip {{
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  background: rgba(30, 41, 59, 0.65);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}
.ticker-cell {{
  padding: 10px 14px;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  justify-content: center;
}}
.ticker-cell:last-child {{
  border-right: none;
}}
.ticker-label {{
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: {c['muted']};
  margin-bottom: 3px;
}}
.ticker-value {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.1;
}}
.ticker-sub {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: {c['muted']};
  margin-top: 3px;
}}

/* ---------- KHỐI SCORECARDS ĐỊNH LƯỢNG (HIỆU ỨNG KÍNH MỜ + METER) ---------- */
.scorecard {{
  background: rgba(30, 41, 59, 0.70);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 120px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.25);
  transition: transform 0.2s ease, border-color 0.2s ease;
}}
.scorecard:hover {{
  border-color: rgba(255, 255, 255, 0.16);
  transform: translateY(-2px);
}}
.scorecard-label {{
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: {c['muted']};
  margin-bottom: 6px;
}}
.scorecard-value {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 26px;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 4px;
}}
.scorecard-sub {{
  font-size: 11.5px;
  color: #CBD5E1;
}}
.mini-meter-track {{
  width: 100%;
  height: 5px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
  margin-top: 8px;
}}
.mini-meter-fill {{
  height: 100%;
  border-radius: 3px;
}}

/* ---------- THẺ DỮ LIỆU CHUNG (GLASSMORPHISM) ---------- */
.glass-panel {{
  background: rgba(30, 41, 59, 0.65);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 12px;
}}

/* ---------- NÚT NHẤN TINH TẾ (SLATE & GOLD) ---------- */
.stButton > button {{
  background: #1E293B !important;
  color: #F8FAFC !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  font-weight: 600 !important;
  border-radius: 6px !important;
  padding: 6px 14px !important;
  font-size: 12.5px !important;
  transition: all 0.2s ease !important;
}}
.stButton > button:hover {{
  background: #334155 !important;
  border-color: rgba(216, 180, 95, 0.6) !important;
  color: {c['gold']} !important;
}}
.stButton > button[kind="primary"] {{
  background: {c['gold']} !important;
  color: #1E1B18 !important;
  border: none !important;
  font-weight: 700 !important;
}}
.stButton > button[kind="primary"]:hover {{
  background: {c['gold_hover']} !important;
  box-shadow: 0 4px 14px rgba(216, 180, 95, 0.4) !important;
}}

/* Thẻ 12 chỉ số */
.metric-card {{
  background: rgba(30, 41, 59, 0.65);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-left: 3px solid {c['accent']};
  border-radius: 6px;
  padding: 12px 14px;
  margin-bottom: 10px;
}}
.metric-no {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: {c['muted']};
}}
.metric-name {{
  font-size: 13px;
  font-weight: 600;
  margin: 2px 0 4px 0;
}}
.metric-value {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 16.5px;
  font-weight: 700;
  color: {c['text']};
}}
.metric-note {{
  font-size: 11.5px;
  color: {c['muted']};
  margin-top: 4px;
  line-height: 1.45;
}}

/* Nhãn trạng thái */
.badge {{
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.03em;
}}

/* Bảng */
.stDataFrame, .stTable {{
  font-family: 'JetBrains Mono', monospace;
}}

/* Footnote */
.footnote {{
  font-size: 11px;
  color: {c['muted']};
  line-height: 1.6;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 12px;
  margin-top: 20px;
}}
</style>
"""


def plotly_layout(height: int = 380, title: str = "") -> dict:
    """Layout Plotly kính mờ đồng bộ hoàn hảo với theme Glassmorphism."""
    c = COLORS
    return dict(
        height=height,
        title=dict(text=title, font=dict(size=13.5, color=c["text"], family="Plus Jakarta Sans, Be Vietnam Pro")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30, 41, 59, 0.45)",
        font=dict(family="JetBrains Mono, monospace", size=11, color=c["muted"]),
        margin=dict(l=12, r=12, t=42 if title else 14, b=12),
        xaxis=dict(gridcolor="rgba(255, 255, 255, 0.06)", zerolinecolor="rgba(255, 255, 255, 0.08)", showspikes=False),
        yaxis=dict(gridcolor="rgba(255, 255, 255, 0.06)", zerolinecolor="rgba(255, 255, 255, 0.08)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        hoverlabel=dict(bgcolor="#1E293B", font_size=11,
                        font_family="JetBrains Mono, monospace"),
    )
