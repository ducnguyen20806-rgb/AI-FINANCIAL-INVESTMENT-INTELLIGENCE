"""
Module6/decision_engine.py
AI DECISION ENGINE — Bộ điều phối trung tâm.

Luồng xử lý:
    Module 1 (dữ liệu thô)
        -> Module 2 (cơ bản)
        -> Module 5 (rủi ro: cần Beta trước khi tính WACC)
        -> Module 3 (định giá: dùng Beta từ Module 5)
        -> Module 4 (kỹ thuật)
        -> Module 6 ML (kịch bản giá + chấm điểm)
        -> Đóng gói: 12 chỉ số cốt lõi + khuyến nghị + nhật ký đầu tư

Toàn bộ kết quả là số liệu tính toán — không có nhận định định tính cảm tính.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from Module1.data_source import get_data_source
from Module2.fundamental_engine import FundamentalEngine
from Module3.valuation_engine import ValuationEngine
from Module4.technical_engine import TechnicalEngine
from Module5.risk_engine import RiskEngine
from Module6.ml_financial_engine import MLFinancialEngine
from common.utils import clamp, fmt_vnd, pct, rnd, safe_div, safe_float
from config import finance_config

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Bộ não tích hợp toán tài chính và Machine Learning."""

    def __init__(self, data_source=None, config=finance_config) -> None:
        self.cfg = config
        self.data_source = data_source or get_data_source()
        self.fundamental = FundamentalEngine()
        self.valuation = ValuationEngine(config)
        self.technical = TechnicalEngine()
        self.risk = RiskEngine(config)
        self.ml = MLFinancialEngine(config)

    # ------------------------------------------------------------------
    def analyze(self, symbol: str, raw: dict[str, Any] | None = None) -> dict[str, Any]:
        """Phân tích trọn vẹn một mã cổ phiếu và trả về JSON chuẩn."""
        started = time.perf_counter()
        symbol = symbol.upper().strip()

        raw = raw or self.data_source.get_all_stock_data(symbol)
        quote = raw.get("quote") or {}
        ohlc = raw.get("ohlc") or []
        index_ohlc = raw.get("index_ohlc") or []
        financials = raw.get("financials") or {}

        # --- Module 2: Cơ bản ---
        fundamentals = self.fundamental.analyze(financials)

        # --- Vốn hoá tạm tính để phục vụ Altman X4 ---
        price = safe_float(quote.get("price"))
        shares = safe_float(financials.get("shares_outstanding"))
        market_cap = price * shares

        # --- Module 5: Rủi ro (lấy Beta cho WACC) ---
        risk = self.risk.analyze(financials, ohlc, index_ohlc, market_cap, fundamentals)
        beta = safe_float(risk.get("market", {}).get("beta"), self.cfg.default_beta)

        # --- Module 3: Định giá ---
        valuation = self.valuation.analyze(fundamentals, quote, financials, beta)
        fundamentals["eps_ttm"] = valuation["eps"]

        # --- Module 4: Kỹ thuật ---
        technical = self.technical.analyze(ohlc)

        # --- Module 6: ML ---
        scenarios = self.ml.predict_scenarios(ohlc)
        score = self.ml.investment_score(fundamentals, valuation, risk, technical)

        # --- Tổng hợp ---
        metrics12 = self.build_12_metrics(fundamentals, valuation, risk, technical, price)
        recommendation = self.build_recommendation(score, valuation, risk, scenarios, price)
        journal = self.build_thesis_journal(symbol, price, valuation, risk, scenarios,
                                            recommendation, score)

        elapsed = (time.perf_counter() - started) * 1000
        return {
            "symbol": symbol,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "data_source": raw.get("source", "UNKNOWN"),
            "warnings": raw.get("warnings", []),
            "elapsed_ms": rnd(elapsed, 1),
            "quote": quote,
            "fundamentals": fundamentals,
            "valuation": valuation,
            "technical": technical,
            "risk": risk,
            "scenarios": scenarios,
            "investment_score": score,
            "metrics_12": metrics12,
            "recommendation": recommendation,
            "thesis_journal": journal,
        }

    # ------------------------------------------------------------------
    # 12 chỉ số phân tích cốt lõi
    # ------------------------------------------------------------------
    def build_12_metrics(self, f: dict[str, Any], v: dict[str, Any], r: dict[str, Any],
                         t: dict[str, Any], price: float) -> list[dict[str, Any]]:
        z = r.get("altman", {})
        wacc_detail = v.get("wacc_detail", {})

        return [
            {
                "no": 1, "key": "business_model", "name": "Mô hình kinh doanh",
                "value": f"Biên EBIT {pct(f.get('ebit_margin'))}%",
                "raw": f.get("ebit_margin"),
                "note": f"EBIT TTM {fmt_vnd(f.get('ebit_ttm'))} trên doanh thu {fmt_vnd(f.get('revenue_ttm'))}.",
            },
            {
                "no": 2, "key": "competitive_moat", "name": "Lợi thế cạnh tranh",
                "value": f"ROIC {pct(f.get('roic'))}%",
                "raw": f.get("roic"),
                "note": f"So với WACC {pct(v.get('wacc'))}% — chênh lệch "
                        f"{pct(safe_float(f.get('roic')) - safe_float(v.get('wacc')))} điểm %.",
            },
            {
                "no": 3, "key": "revenue_growth", "name": "Tăng trưởng doanh thu",
                "value": f"CAGR {pct(f.get('revenue_cagr'))}%",
                "raw": f.get("revenue_cagr"),
                "note": f"Tính trên {f.get('cagr_years')} năm; YoY quý gần nhất "
                        f"{pct(f.get('revenue_growth_yoy'))}%.",
            },
            {
                "no": 4, "key": "earnings_quality", "name": "Chất lượng lợi nhuận",
                "value": f"CFO/LNST {rnd(f.get('cfo_to_net_income'))} lần",
                "raw": f.get("cfo_to_net_income"),
                "note": "Trên 1.0 lần: lợi nhuận được hỗ trợ bởi dòng tiền thực.",
            },
            {
                "no": 5, "key": "cash_flow_reality", "name": "Dòng tiền tự do",
                "value": fmt_vnd(f.get("free_cash_flow")),
                "raw": f.get("free_cash_flow"),
                "note": f"FCF = CFO {fmt_vnd(f.get('cfo_ttm'))} - Capex {fmt_vnd(f.get('capex_ttm'))}.",
            },
            {
                "no": 6, "key": "roe_roic", "name": "Hiệu quả sử dụng vốn",
                "value": f"ROE {pct(f.get('roe'))}% | ROIC {pct(f.get('roic'))}%",
                "raw": f.get("roe"),
                "note": f"ROA {pct(f.get('roa'))}%.",
            },
            {
                "no": 7, "key": "debt_health", "name": "Sức khoẻ nợ vay",
                "value": f"Altman Z = {z.get('z_score')} ({z.get('zone')})",
                "raw": z.get("z_score"),
                "note": z.get("description", ""),
            },
            {
                "no": 8, "key": "valuation", "name": "Định giá",
                "value": f"P/E {v.get('pe')} | DCF {fmt_vnd(v.get('intrinsic_value'))}/CP",
                "raw": v.get("intrinsic_value"),
                "note": f"P/B {v.get('pb')}; P/E ngành {v.get('peer_pe')}.",
            },
            {
                "no": 9, "key": "catalysts", "name": "Động lực tăng trưởng",
                "value": f"g(FCF) {pct(v.get('dcf', {}).get('growth_used'))}% | WACC {pct(v.get('wacc'))}%",
                "raw": v.get("dcf", {}).get("growth_used"),
                "note": f"Re {pct(wacc_detail.get('cost_of_equity'))}%, "
                        f"Rd {pct(wacc_detail.get('cost_of_debt'))}%, Beta {wacc_detail.get('beta_used')}.",
            },
            {
                "no": 10, "key": "major_risks", "name": "Rủi ro chính",
                "value": f"Nợ vay/VCSH {rnd(f.get('debt_to_equity'))} lần",
                "raw": f.get("debt_to_equity"),
                "note": "; ".join(r.get("risk_flags", [])) or "Không phát hiện cờ rủi ro nổi bật.",
            },
            {
                "no": 11, "key": "thesis_invalidation", "name": "Ngưỡng phủ định luận điểm",
                "value": f"Cắt lỗ tại {fmt_vnd(price * self.cfg.stop_loss_ratio)}",
                "raw": rnd(price * self.cfg.stop_loss_ratio, 0),
                "note": f"Tương ứng -{pct(1 - self.cfg.stop_loss_ratio, 0)}% so với thị giá; "
                        f"hỗ trợ kỹ thuật {fmt_vnd(t.get('support'))}.",
            },
            {
                "no": 12, "key": "fair_buy_price", "name": "Vùng giá mua hợp lý",
                "value": fmt_vnd(v.get("fair_buy_price")),
                "raw": v.get("fair_buy_price"),
                "note": f"Giá trị hợp lý {fmt_vnd(v.get('fair_value'))} trừ biên an toàn 15%.",
            },
        ]

    # ------------------------------------------------------------------
    # Khuyến nghị & quản trị vị thế
    # ------------------------------------------------------------------
    def build_recommendation(self, score: dict[str, Any], v: dict[str, Any],
                             r: dict[str, Any], s: dict[str, Any],
                             price: float) -> dict[str, Any]:
        overall = safe_float(score.get("overall_score"))
        upside = safe_float(v.get("upside"))
        z_zone = r.get("altman", {}).get("zone", "")

        if overall >= 70 and upside > 0.15 and z_zone != "RỦI RO CAO":
            action, conviction = "MUA", "Cao"
        elif overall >= 55 and upside > 0.0:
            action, conviction = "TÍCH LUỸ", "Trung bình"
        elif overall >= 40:
            action, conviction = "NẮM GIỮ / THEO DÕI", "Trung bình"
        elif upside < -0.10 or z_zone == "RỦI RO CAO":
            action, conviction = "BÁN / TRÁNH", "Cao"
        else:
            action, conviction = "GIẢM TỶ TRỌNG", "Thấp"

        # Position sizing: tỷ lệ thuận điểm số, nghịch với biến động
        vol = safe_float(r.get("market", {}).get("annual_volatility"), 0.30)
        base_size = (overall / 100.0) * self.cfg.max_position_size
        vol_adj = clamp(safe_div(0.30, max(vol, 0.05), default=1.0), 0.4, 1.5)
        position_size = clamp(base_size * vol_adj, 0.0, self.cfg.max_position_size)

        target = safe_float(v.get("fair_value")) or safe_float(s.get("base_case"))
        stop = price * self.cfg.stop_loss_ratio
        reward = target - price
        risk_amount = price - stop
        rr = safe_div(reward, risk_amount)

        return {
            "action": action,
            "conviction": conviction,
            "overall_score": overall,
            "grade": score.get("grade"),
            "target_price": rnd(target, 0),
            "stop_price": rnd(stop, 0),
            "entry_zone_low": rnd(safe_float(v.get("fair_buy_price")) * 0.97, 0),
            "entry_zone_high": rnd(safe_float(v.get("fair_buy_price")) * 1.03, 0),
            "risk_reward_ratio": rnd(rr, 2),
            "position_size_pct": rnd(position_size * 100, 2),
            "expected_upside_pct": pct(upside),
            "rationale": [
                f"Investment Score {overall}/100 ({score.get('grade')}).",
                f"Giá trị hợp lý {fmt_vnd(v.get('fair_value'))} so với thị giá {fmt_vnd(price)} "
                f"— chênh lệch {pct(upside)}%.",
                f"Altman Z-Score {r.get('altman', {}).get('z_score')} — {z_zone}.",
                f"Kịch bản cơ sở {fmt_vnd(s.get('base_case'))} sau "
                f"{s.get('meta', {}).get('horizon_days')} phiên.",
                f"Tỷ lệ Lợi nhuận/Rủi ro {rnd(rr, 2)} lần.",
            ],
        }

    # ------------------------------------------------------------------
    # Nhật ký đầu tư
    # ------------------------------------------------------------------
    def build_thesis_journal(self, symbol: str, price: float, v: dict[str, Any],
                             r: dict[str, Any], s: dict[str, Any],
                             rec: dict[str, Any], score: dict[str, Any]) -> dict[str, Any]:
        z = r.get("altman", {})
        return {
            "symbol": symbol,
            "entry_date": datetime.now().strftime("%d/%m/%Y"),
            "entry_price": rnd(price, 0),
            "thesis": (
                f"Định giá DCF cho giá trị nội tại {fmt_vnd(v.get('intrinsic_value'))}/CP "
                f"(WACC {pct(v.get('wacc'))}%, g cuối kỳ {pct(v.get('dcf', {}).get('terminal_growth'))}%), "
                f"chênh lệch {pct(v.get('upside'))}% so với thị giá. "
                f"Altman Z-Score {z.get('z_score')} — {z.get('zone')}."
            ),
            "catalysts": (
                f"Tăng trưởng FCF giả định {pct(v.get('dcf', {}).get('growth_used'))}%/năm; "
                f"P/E hiện tại {v.get('pe')} so với P/E ngành {v.get('peer_pe')}."
            ),
            "bear_risk": (
                f"Kịch bản Bear {fmt_vnd(s.get('bear_case'))} "
                f"({pct(s.get('bear_return'))}%); "
                + ("; ".join(r.get("risk_flags", [])) or "không có cờ rủi ro nổi bật.")
            ),
            "target_price": rec.get("target_price"),
            "stop_loss": rec.get("stop_price"),
            "position_size_pct": rec.get("position_size_pct"),
            "status": "ĐỀ XUẤT MỞ VỊ THẾ" if rec.get("action") in ("MUA", "TÍCH LUỸ") else "CHƯA MỞ VỊ THẾ",
            "score_snapshot": score.get("pillars", {}),
        }


_engine: DecisionEngine | None = None


def get_engine() -> DecisionEngine:
    """Singleton engine dùng chung cho API Gateway và giao diện Streamlit."""
    global _engine
    if _engine is None:
        _engine = DecisionEngine()
    return _engine
