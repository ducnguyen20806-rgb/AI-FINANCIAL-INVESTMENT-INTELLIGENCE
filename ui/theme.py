"""
ui/theme.py
Hệ thống thị giác của nền tảng.

Bảng màu lấy trực tiếp từ quy ước bảng giá chứng khoán Việt Nam (HOSE/HNX):
tím = giá trần, xanh lá = tăng, vàng = tham chiếu, đỏ = giảm, xanh lơ = sàn.
Người dùng Việt Nam đọc màu này theo phản xạ, nên toàn bộ số liệu giá trong
giao diện đều tuân thủ đúng quy ước đó thay vì dùng bảng màu chung chung.

Chữ: Be Vietnam Pro (hiển thị & nội dung, hỗ trợ đầy đủ dấu tiếng Việt),
JetBrains Mono (số liệu — chữ số đều bề rộng nên các cột số thẳng hàng).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Bảng màu
# ---------------------------------------------------------------------------
COLORS = {
    "ink": "#0A0E14",        # nền bảng điện
    "panel": "#121821",      # nền thẻ
    "panel_alt": "#0F141C",
    "line": "#1E2733",       # đường kẻ
    "text": "#E4EAF2",
    "muted": "#8494A8",
    "ceiling": "#B44BFF",    # giá trần
    "up": "#00C566",         # tăng giá
    "reference": "#F5C518",  # tham chiếu
    "down": "#FF4D4D",       # giảm giá
    "floor": "#00C2D1",      # giá sàn
    "accent": "#4C8DFF",     # điểm nhấn trung tính (không mang nghĩa tăng/giảm)
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
    """Trả về mã màu của một mức giá theo đúng quy ước bảng điện."""
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
    if score >= 70:
        return COLORS["up"]
    if score >= 50:
        return COLORS["reference"]
    if score >= 35:
        return "#FF8A3D"
    return COLORS["down"]


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
def build_css() -> str:
    c = COLORS
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {{
  --ink: {c['ink']};
  --panel: {c['panel']};
  --line: {c['line']};
  --text: {c['text']};
  --muted: {c['muted']};
  --up: {c['up']};
  --down: {c['down']};
  --ref: {c['reference']};
  --ceiling: {c['ceiling']};
  --floor: {c['floor']};
  --accent: {c['accent']};
}}

.stApp {{
  background: var(--ink);
  color: var(--text);
  font-family: 'Be Vietnam Pro', system-ui, sans-serif;
}}

section[data-testid="stSidebar"] {{
  background: {c['panel_alt']};
  border-right: 1px solid var(--line);
}}

h1, h2, h3, h4 {{
  font-family: 'Be Vietnam Pro', sans-serif;
  letter-spacing: -0.02em;
  color: var(--text);
}}

/* ---------- Thanh tiêu đề mã cổ phiếu ---------- */
.symbol-head {{
  display: flex; align-items: baseline; gap: 14px;
  padding: 4px 0 10px 0;
}}
.symbol-code {{
  font-size: 46px; font-weight: 800; line-height: 1;
  letter-spacing: -0.03em;
}}
.symbol-meta {{
  font-size: 13px; color: var(--muted);
  font-family: 'JetBrains Mono', monospace;
}}

/* ---------- Dải bảng giá (signature) ---------- */
.price-board {{
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  border: 1px solid var(--line);
  border-radius: 6px;
  overflow: hidden;
  background: var(--panel);
  margin-bottom: 18px;
}}
.pb-cell {{
  padding: 12px 14px;
  border-right: 1px solid var(--line);
}}
.pb-cell:last-child {{ border-right: none; }}
.pb-label {{
  font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.14em;
  color: var(--muted); margin-bottom: 6px;
}}
.pb-value {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px; font-weight: 700; line-height: 1.1;
}}
.pb-sub {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px; color: var(--muted); margin-top: 3px;
}}

/* ---------- Thẻ số liệu ---------- */
.kpi {{
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 14px 16px;
  height: 100%;
}}
.kpi-label {{
  font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.14em;
  color: var(--muted); margin-bottom: 8px;
}}
.kpi-value {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 26px; font-weight: 700; line-height: 1.15;
}}
.kpi-note {{ font-size: 12px; color: var(--muted); margin-top: 6px; }}

/* ---------- Thanh điểm 5 trụ cột ---------- */
.pillar-row {{ margin-bottom: 12px; }}
.pillar-top {{
  display: flex; justify-content: space-between;
  font-size: 12.5px; margin-bottom: 5px;
}}
.pillar-name {{ color: var(--text); }}
.pillar-num {{ font-family: 'JetBrains Mono', monospace; color: var(--muted); }}
.pillar-track {{
  height: 7px; background: #1A222D; border-radius: 4px; overflow: hidden;
}}
.pillar-fill {{ height: 100%; border-radius: 4px; }}

/* ---------- Thẻ 12 chỉ số ---------- */
.metric-card {{
  background: var(--panel);
  border: 1px solid var(--line);
  border-left: 3px solid var(--accent);
  border-radius: 4px;
  padding: 12px 14px;
  margin-bottom: 10px;
}}
.metric-no {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; color: var(--muted);
}}
.metric-name {{ font-size: 13.5px; font-weight: 600; margin: 2px 0 6px 0; }}
.metric-value {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 17px; font-weight: 700; color: var(--text);
}}
.metric-note {{ font-size: 12px; color: var(--muted); margin-top: 6px; line-height: 1.5; }}

/* ---------- Nhãn trạng thái ---------- */
.badge {{
  display: inline-block; padding: 4px 11px; border-radius: 3px;
  font-size: 12px; font-weight: 600; letter-spacing: 0.03em;
}}

/* ---------- Bảng ---------- */
.stDataFrame, .stTable {{ font-family: 'JetBrains Mono', monospace; }}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {{
  gap: 2px; border-bottom: 1px solid var(--line);
}}
.stTabs [data-baseweb="tab"] {{
  background: transparent; color: var(--muted);
  font-size: 13.5px; padding: 9px 16px;
}}
.stTabs [aria-selected="true"] {{
  color: var(--text); border-bottom: 2px solid var(--accent);
}}

/* ---------- Nút ---------- */
.stButton > button {{
  background: var(--accent); color: #06101F; border: none;
  font-weight: 600; border-radius: 4px; width: 100%;
}}
.stButton > button:hover {{ background: #6BA1FF; color: #06101F; }}

/* ---------- Ghi chú nhỏ ---------- */
.footnote {{
  font-size: 11.5px; color: var(--muted); line-height: 1.6;
  border-top: 1px solid var(--line); padding-top: 12px; margin-top: 22px;
}}

/* Ẩn menu mặc định của Streamlit */
#MainMenu, footer {{ visibility: hidden; }}
</style>
"""


def plotly_layout(height: int = 380, title: str = "") -> dict:
    """Layout Plotly dùng chung, đồng bộ với theme."""
    c = COLORS
    return dict(
        height=height,
        title=dict(text=title, font=dict(size=14, color=c["text"], family="Be Vietnam Pro")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=c["panel"],
        font=dict(family="JetBrains Mono, monospace", size=11, color=c["muted"]),
        margin=dict(l=10, r=10, t=40 if title else 14, b=10),
        xaxis=dict(gridcolor=c["line"], zerolinecolor=c["line"], showspikes=False),
        yaxis=dict(gridcolor=c["line"], zerolinecolor=c["line"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        hoverlabel=dict(bgcolor=c["panel"], font_size=11,
                        font_family="JetBrains Mono, monospace"),
    )
