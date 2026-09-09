"""
ui/charts.py
Bộ biểu đồ Plotly dùng cho giao diện Streamlit.

Mọi biểu đồ đều nhận thẳng payload JSON do Module 6 trả về, không tự tính
lại số liệu — tầng giao diện chỉ trình bày, không chứa logic tài chính.
"""
from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from common.utils import safe_float
from ui.theme import COLORS, PILLAR_LABELS, plotly_layout, score_color


def _add_hline(fig: go.Figure, **kwargs: Any) -> None:
    """Helper gọi add_hline tránh lỗi type stub row/col của plotly."""
    fig_any: Any = fig
    fig_any.add_hline(**kwargs)


def candlestick_chart(technical: dict[str, Any], months: int = 12) -> go.Figure:
    """Biểu đồ nến + EMA20/EMA50 + khối lượng + vùng hỗ trợ/kháng cự."""
    s = technical.get("series") or {}
    dates = s.get("date") or []
    closes = s.get("close") or []
    if not dates or not closes:
        return _empty_fig("Không có dữ liệu nến.")

    n = min(len(dates), len(closes), months * 21)
    if n == 0:
        return _empty_fig("Không có dữ liệu nến.")
    sl = slice(-n, None)

    opens = s.get("open") or closes
    highs = s.get("high") or closes
    lows = s.get("low") or closes
    volumes = s.get("volume") or [0] * len(closes)

    open_slice = opens[sl] if len(opens) >= n else closes[sl]
    high_slice = highs[sl] if len(highs) >= n else closes[sl]
    low_slice = lows[sl] if len(lows) >= n else closes[sl]
    close_slice = closes[sl]
    vol_slice = volumes[sl] if len(volumes) >= n else [0] * n

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.74, 0.26], vertical_spacing=0.03,
    )

    fig.add_trace(
        go.Candlestick(
            x=dates[sl], open=open_slice, high=high_slice,
            low=low_slice, close=close_slice, name="Giá",
            increasing=dict(line=dict(color=COLORS["up"], width=1),
                            fillcolor=COLORS["up"]),
            decreasing=dict(line=dict(color=COLORS["down"], width=1),
                            fillcolor=COLORS["down"]),
        ),
        row=1, col=1,
    )
    for key, label, color in (("ema20", "EMA20", COLORS["accent"]),
                              ("ema50", "EMA50", COLORS["ceiling"])):
        series_val = s.get(key)
        if series_val and len(series_val) >= n:
            fig.add_trace(
                go.Scatter(x=dates[sl], y=series_val[sl], name=label, mode="lines",
                           line=dict(color=color, width=1.4)),
                row=1, col=1,
            )

    support = safe_float(technical.get("support", 0))
    resistance = safe_float(technical.get("resistance", 0))
    for level, label, color in ((resistance, "Kháng cự", COLORS["down"]),
                                (support, "Hỗ trợ", COLORS["up"])):
        if level > 0:
            _add_hline(fig, y=level, line=dict(color=color, width=1, dash="dot"),
                       annotation_text=f"{label} {level:,.0f}",
                       annotation_font=dict(size=10, color=color),
                       annotation_position="right", row=1, col=1)

    vol_colors = [COLORS["up"] if safe_float(c) >= safe_float(o) else COLORS["down"]
                  for c, o in zip(close_slice, open_slice)]
    fig.add_trace(
        go.Bar(x=dates[sl], y=vol_slice, name="Khối lượng",
               marker=dict(color=vol_colors), opacity=0.55),
        row=2, col=1,
    )

    layout = plotly_layout(height=470)
    layout.pop("xaxis", None)
    layout.pop("yaxis", None)
    fig.update_layout(**layout, xaxis_rangeslider_visible=False, showlegend=True, barmode="overlay")
    fig.update_xaxes(gridcolor=COLORS["line"], showgrid=False)
    fig.update_yaxes(gridcolor=COLORS["line"], row=1, col=1, title_text="Giá (VNĐ)")
    fig.update_yaxes(gridcolor=COLORS["line"], row=2, col=1, title_text="KL")
    return fig


def momentum_chart(technical: dict[str, Any], months: int = 6) -> go.Figure:
    """RSI(14) Wilder và MACD trên cùng một khung."""
    s = technical.get("series") or {}
    dates = s.get("date") or []
    rsi_vals = s.get("rsi14") or []
    if not dates or not rsi_vals:
        return _empty_fig("Không có dữ liệu chỉ báo.")

    n = min(len(dates), len(rsi_vals), months * 21)
    if n == 0:
        return _empty_fig("Không có dữ liệu chỉ báo.")
    sl = slice(-n, None)

    macd_vals = s.get("macd") or []
    sig_vals = s.get("macd_signal") or []
    hist_vals = s.get("macd_hist") or []

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.5, 0.5], vertical_spacing=0.08,
                        subplot_titles=("RSI 14 (Wilder)", "MACD 12-26-9"))

    fig.add_trace(go.Scatter(x=dates[sl], y=rsi_vals[sl], name="RSI",
                             line=dict(color=COLORS["accent"], width=1.5)), row=1, col=1)
    _add_hline(fig, y=70, line=dict(color=COLORS["down"], width=1, dash="dot"), row=1, col=1)
    _add_hline(fig, y=30, line=dict(color=COLORS["up"], width=1, dash="dot"), row=1, col=1)
    _add_hline(fig, y=50, line=dict(color=COLORS["line"], width=1), row=1, col=1)

    if len(macd_vals) >= n:
        fig.add_trace(go.Scatter(x=dates[sl], y=macd_vals[sl], name="MACD",
                                 line=dict(color=COLORS["reference"], width=1.5)), row=2, col=1)
    if len(sig_vals) >= n:
        fig.add_trace(go.Scatter(x=dates[sl], y=sig_vals[sl], name="Signal",
                                 line=dict(color=COLORS["ceiling"], width=1.3)), row=2, col=1)
    if len(hist_vals) >= n:
        hist = hist_vals[sl]
        hist_colors = [COLORS["up"] if safe_float(h) >= 0 else COLORS["down"] for h in hist]
        fig.add_trace(go.Bar(x=dates[sl], y=hist, name="Histogram",
                             marker=dict(color=hist_colors), opacity=0.5), row=2, col=1)

    layout = plotly_layout(height=420)
    layout.pop("xaxis", None)
    layout.pop("yaxis", None)
    fig.update_layout(**layout, showlegend=True)
    fig.update_annotations(font=dict(size=11, color=COLORS["muted"]))
    fig.update_xaxes(gridcolor=COLORS["line"], showgrid=False)
    fig.update_yaxes(gridcolor=COLORS["line"], range=[0, 100], row=1, col=1)
    fig.update_yaxes(gridcolor=COLORS["line"], row=2, col=1)
    return fig


def scenario_chart(scenarios: dict[str, Any]) -> go.Figure:
    """Ba kịch bản giá Bull / Base / Bear so với thị giá hiện tại."""
    current = scenarios.get("current_price", 0)
    labels = ["Bear Case", "Base Case", "Bull Case"]
    values = [scenarios.get("bear_case", 0), scenarios.get("base_case", 0),
              scenarios.get("bull_case", 0)]
    rets = [scenarios.get("bear_return", 0), scenarios.get("base_return", 0),
            scenarios.get("bull_return", 0)]
    colors = [COLORS["down"], COLORS["reference"], COLORS["up"]]

    fig = go.Figure(
        go.Bar(
            x=labels, y=values, marker=dict(color=colors),
            text=[f"{v:,.0f}<br>{r * 100:+.1f}%" for v, r in zip(values, rets)],
            textposition="outside",
            textfont=dict(size=12, color=COLORS["text"]),
            hovertemplate="%{x}: %{y:,.0f} VNĐ<extra></extra>",
        )
    )
    if current:
        fig.add_hline(y=current, line=dict(color=COLORS["text"], width=1.2, dash="dash"),
                      annotation_text=f"Thị giá {current:,.0f}",
                      annotation_font=dict(size=11, color=COLORS["text"]))

    layout = plotly_layout(height=330)
    fig.update_layout(**layout, showlegend=False)
    fig.update_yaxes(title_text="VNĐ", rangemode="tozero")
    return fig


def pillar_chart(score: dict[str, Any]) -> go.Figure:
    """Điểm 5 trụ cột dạng thanh ngang."""
    pillars = score.get("pillars", {})
    keys = ["fundamental", "valuation", "risk", "quality", "momentum"]
    labels = [f"{PILLAR_LABELS[k]} ({score.get('weights', {}).get(k, 0) * 100:.0f}%)"
              for k in keys]
    values = [pillars.get(k, 0) for k in keys]

    fig = go.Figure(
        go.Bar(
            x=values, y=labels, orientation="h",
            marker=dict(color=[score_color(v) for v in values]),
            text=[f"{v:.1f}" for v in values],
            textposition="outside",
            textfont=dict(size=11, color=COLORS["text"]),
            hovertemplate="%{y}: %{x:.1f}/100<extra></extra>",
        )
    )
    layout = plotly_layout(height=290)
    fig.update_layout(**layout, showlegend=False)
    fig.update_xaxes(range=[0, 112], title_text="Điểm (0 - 100)")
    fig.update_yaxes(autorange="reversed")
    return fig


def dcf_chart(dcf: dict[str, Any]) -> go.Figure:
    """Dòng tiền dự báo và giá trị hiện tại theo từng năm."""
    proj = dcf.get("projection") or []
    if not proj:
        return _empty_fig("Mô hình DCF không áp dụng được (FCF cơ sở âm).")

    years = [f"Năm {p['year']}" for p in proj]
    fcf = [p["fcf"] for p in proj]
    pv = [p["present_value"] for p in proj]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=fcf, name="FCF dự báo",
                         marker=dict(color=COLORS["line"]),
                         hovertemplate="%{x}: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=years, y=pv, name="Giá trị hiện tại (PV)",
                         marker=dict(color=COLORS["accent"]),
                         hovertemplate="%{x}: %{y:,.0f}<extra></extra>"))

    layout = plotly_layout(height=320)
    fig.update_layout(**layout, barmode="overlay", showlegend=True)
    fig.update_yaxes(title_text="VNĐ")
    return fig


def financial_history_chart(history: list[dict[str, Any]]) -> go.Figure:
    """Doanh thu, LNST, CFO theo quý + biên lợi nhuận ròng."""
    if not history:
        return _empty_fig("Không có lịch sử báo cáo tài chính.")

    periods = [str(h.get("period", "")) for h in history]
    revs = [safe_float(h.get("revenue")) for h in history]
    nis = [safe_float(h.get("net_income")) for h in history]
    cfos = [safe_float(h.get("cfo")) for h in history]
    margins = [safe_float(h.get("net_margin")) * 100 for h in history]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(x=periods, y=revs, name="Doanh thu",
                         marker=dict(color=COLORS["line"])), secondary_y=False)
    fig.add_trace(go.Bar(x=periods, y=nis, name="LNST",
                         marker=dict(color=COLORS["accent"])), secondary_y=False)
    fig.add_trace(go.Scatter(x=periods, y=cfos, name="CFO",
                             mode="lines+markers",
                             line=dict(color=COLORS["reference"], width=1.6)),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=periods, y=margins,
                             name="Biên LN ròng (%)", mode="lines",
                             line=dict(color=COLORS["ceiling"], width=1.6, dash="dot")),
                  secondary_y=True)

    layout = plotly_layout(height=360)
    layout.pop("yaxis", None)
    fig.update_layout(**layout, barmode="group", showlegend=True)
    fig.update_yaxes(title_text="VNĐ", secondary_y=False, gridcolor=COLORS["line"])
    fig.update_yaxes(title_text="%", secondary_y=True, showgrid=False)
    return fig


def wacc_chart(wacc_detail: dict[str, Any]) -> go.Figure:
    """Cơ cấu chi phí vốn: tỷ trọng và chi phí từng cấu phần."""
    labels = ["Vốn chủ sở hữu (Re)", "Nợ vay sau thuế (Rd)"]
    tax = safe_float(wacc_detail.get("tax_rate", 0.20))
    weights = [safe_float(wacc_detail.get("weight_equity", 0)) * 100,
               safe_float(wacc_detail.get("weight_debt", 0)) * 100]
    costs = [safe_float(wacc_detail.get("cost_of_equity", 0)) * 100,
             safe_float(wacc_detail.get("cost_of_debt", 0)) * (1 - tax) * 100]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=labels, y=weights, name="Tỷ trọng (%)",
                         marker=dict(color=COLORS["line"]),
                         text=[f"{w:.1f}%" for w in weights], textposition="inside"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=labels, y=costs, name="Chi phí vốn (%)",
                             mode="markers+text",
                             marker=dict(color=COLORS["reference"], size=14),
                             text=[f"{c:.2f}%" for c in costs], textposition="top center",
                             textfont=dict(color=COLORS["text"], size=11)),
                  secondary_y=True)

    layout = plotly_layout(height=300)
    layout.pop("yaxis", None)
    fig.update_layout(**layout, showlegend=True)
    fig.update_yaxes(title_text="Tỷ trọng %", range=[0, 110], secondary_y=False,
                     gridcolor=COLORS["line"])
    fig.update_yaxes(title_text="Chi phí %", secondary_y=True, showgrid=False,
                     rangemode="tozero")
    return fig


def drawdown_chart(technical: dict[str, Any]) -> go.Figure:
    """Đường sụt giảm từ đỉnh (drawdown) của giá cổ phiếu."""
    s = technical.get("series") or {}
    closes = [safe_float(c) for c in (s.get("close") or [])]
    dates = [str(d) for d in (s.get("date") or [])]
    if not closes or not dates:
        return _empty_fig("Không có dữ liệu giá.")

    n = min(len(closes), len(dates))
    closes = closes[:n]
    dates = dates[:n]

    peak = closes[0]
    dd = []
    for c in closes:
        peak = max(peak, c)
        dd.append((c / peak - 1.0) * 100 if peak > 0 else 0.0)

    fig = go.Figure(
        go.Scatter(x=dates, y=dd, mode="lines", name="Drawdown",
                   line=dict(color=COLORS["down"], width=1.2),
                   fill="tozeroy", fillcolor="rgba(255,77,77,0.18)",
                   hovertemplate="%{x}: %{y:.2f}%<extra></extra>")
    )
    layout = plotly_layout(height=290)
    fig.update_layout(**layout, showlegend=False)
    fig.update_yaxes(title_text="% từ đỉnh")
    return fig


def _empty_fig(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False,
                       font=dict(color=COLORS["muted"], size=13))
    layout = plotly_layout(height=260)
    fig.update_layout(**layout, showlegend=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def dcf_sensitivity_heatmap(sensitivity: dict[str, Any], current_price: float = 0.0) -> go.Figure:
    """Biểu đồ Heatmap ma trận phân tích độ nhạy định giá DCF 2 chiều: WACC vs Terminal Growth."""
    wacc_labels = sensitivity.get("wacc_labels") or []
    g_labels = sensitivity.get("g_labels") or []
    matrix = sensitivity.get("matrix") or []

    if not wacc_labels or not g_labels or not matrix:
        return _empty_fig("Không có dữ liệu ma trận độ nhạy.")

    text_matrix: list[list[str]] = []
    for row in matrix:
        text_row: list[str] = []
        for val in row:
            if val <= 0:
                text_row.append("N/A")
            else:
                pct_vs_cur = ((val / current_price - 1.0) * 100) if current_price > 0 else 0.0
                text_row.append(f"{val:,.0f}<br>({pct_vs_cur:+.1f}%)")
        text_matrix.append(text_row)

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=g_labels,
            y=wacc_labels,
            text=text_matrix,
            texttemplate="%{text}",
            textfont=dict(size=11, color="#FFFFFF"),
            colorscale=[
                [0.0, "rgba(255, 77, 77, 0.75)"],
                [0.5, "rgba(255, 179, 0, 0.75)"],
                [1.0, "rgba(0, 230, 118, 0.75)"],
            ],
            colorbar=dict(title="Định giá (VNĐ)", tickfont=dict(color=COLORS["text"])),
            hoverongaps=False,
        )
    )
    layout = plotly_layout(
        height=380,
        title="Ma trận Định giá DCF theo Chi phí vốn (WACC) và Tăng trưởng vĩnh viễn (g)",
    )
    fig.update_layout(
        **layout,
        xaxis_title="Tốc độ tăng trưởng dài hạn (g)",
        yaxis_title="Chi phí vốn bình quân (WACC)",
    )
    return fig


def efficient_frontier_chart(opt_data: dict[str, Any]) -> go.Figure:
    """Biểu đồ Đường biên hiệu quả Markowitz (Efficient Frontier) kèm các điểm tối ưu."""
    sample_points = opt_data.get("sample_points") or []
    if not sample_points:
        return _empty_fig("Không có dữ liệu tối ưu danh mục.")

    vols = [safe_float(p.get("volatility")) * 100 for p in sample_points]
    rets = [safe_float(p.get("return")) * 100 for p in sample_points]
    sharpes = [safe_float(p.get("sharpe")) for p in sample_points]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=vols,
            y=rets,
            mode="markers",
            name="Danh mục mô phỏng",
            marker=dict(
                size=6,
                color=sharpes,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Sharpe Ratio", tickfont=dict(color=COLORS["text"])),
                opacity=0.7,
            ),
            hovertemplate="Rủi ro: %{x:.2f}%<br>Lợi suất: %{y:.2f}%<br>Sharpe: %{marker.color:.2f}<extra></extra>",
        )
    )

    max_s = opt_data.get("max_sharpe") or {}
    if max_s:
        fig.add_trace(
            go.Scatter(
                x=[safe_float(max_s.get("volatility")) * 100],
                y=[safe_float(max_s.get("return")) * 100],
                mode="markers+text",
                name="Tối ưu Sharpe",
                text=["★ Max Sharpe"],
                textposition="top center",
                marker=dict(color=COLORS["ceiling"], size=14, symbol="star"),
                hovertemplate="★ Max Sharpe<br>Rủi ro: %{x:.2f}%<br>Lợi suất: %{y:.2f}%<extra></extra>",
            )
        )

    min_v = opt_data.get("min_volatility") or {}
    if min_v:
        fig.add_trace(
            go.Scatter(
                x=[safe_float(min_v.get("volatility")) * 100],
                y=[safe_float(min_v.get("return")) * 100],
                mode="markers+text",
                name="Rủi ro tối thiểu",
                text=["● Min Vol"],
                textposition="bottom center",
                marker=dict(color=COLORS["up"], size=12, symbol="circle"),
                hovertemplate="● Min Volatility<br>Rủi ro: %{x:.2f}%<br>Lợi suất: %{y:.2f}%<extra></extra>",
            )
        )

    layout = plotly_layout(
        height=420,
        title="Đường biên hiệu quả Markowitz (Risk vs Return)",
    )
    fig.update_layout(
        **layout,
        xaxis_title="Độ lệch chuẩn biến động năm (%)",
        yaxis_title="Lợi suất kỳ vọng năm (%)",
        showlegend=True,
    )
    return fig


def multi_ticker_radar_chart(comparison: dict[str, dict[str, float]]) -> go.Figure:
    """Biểu đồ Radar so sánh 5 trụ cột giữa nhiều mã cổ phiếu."""
    if not comparison:
        return _empty_fig("Không có dữ liệu so sánh.")

    categories = list(PILLAR_LABELS.values())
    cat_keys = list(PILLAR_LABELS.keys())

    fig = go.Figure()
    palette = [COLORS["up"], COLORS["accent"], COLORS["ceiling"], COLORS["reference"], "#FF9800", "#E91E63"]

    for idx, (sym, scores) in enumerate(comparison.items()):
        vals = [safe_float(scores.get(k, 50.0)) for k in cat_keys]
        vals.append(vals[0])
        color = palette[idx % len(palette)]

        fig.add_trace(
            go.Scatterpolar(
                r=vals,
                theta=categories + [categories[0]],
                name=sym,
                line=dict(color=color, width=2),
                fill="toself",
                opacity=0.25,
            )
        )

    layout = plotly_layout(
        height=420,
        title="So sánh 5 Trụ cột Investment Score",
    )
    fig.update_layout(
        **layout,
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=COLORS["line"], color=COLORS["muted"]),
            angularaxis=dict(gridcolor=COLORS["line"], color=COLORS["text"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
    )
    return fig
