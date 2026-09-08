"""
Module5/risk_engine.py
RISK & METRICS ENGINE

Đo lường rủi ro nội tại (khả năng phá sản) và rủi ro thị trường (biến động,
Beta, sụt giảm tối đa, VaR).

Altman Z-Score (mô hình 5 biến cho doanh nghiệp niêm yết):

    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 0.999*X5

    X1 = Vốn lưu động thuần / Tổng tài sản
    X2 = Lợi nhuận giữ lại / Tổng tài sản
    X3 = EBIT / Tổng tài sản
    X4 = Giá trị vốn hoá / Tổng nợ phải trả
    X5 = Doanh thu / Tổng tài sản

    Z > 2.99          -> Vùng an toàn (Safe Zone)
    1.81 <= Z <= 2.99 -> Vùng cảnh báo (Grey Zone)
    Z < 1.81          -> Vùng rủi ro cao (Distress Zone)
"""
from __future__ import annotations

from typing import Any

import numpy as np

from common.utils import rnd, safe_div, safe_float, to_returns
from config import finance_config


class RiskEngine:
    """Engine đo lường rủi ro."""

    def __init__(self, config=finance_config) -> None:
        self.cfg = config

    # ------------------------------------------------------------------
    def altman_z_score(self, financials: dict[str, Any], market_cap: float) -> dict[str, Any]:
        periods = financials.get("periods") or []
        if not periods:
            return {"z_score": 0.0, "zone": "KHÔNG XÁC ĐỊNH", "components": {}}

        latest = periods[-1]
        total_assets = safe_float(latest.get("total_assets"))
        current_assets = safe_float(latest.get("current_assets"))
        current_liabilities = safe_float(latest.get("current_liabilities"))
        total_liabilities = safe_float(latest.get("total_liabilities"))
        retained = safe_float(latest.get("retained_earnings"))

        # EBIT và doanh thu lấy theo TTM (4 quý gần nhất)
        window = periods[-4:]
        ebit_ttm = sum(safe_float(p.get("ebit")) for p in window)
        revenue_ttm = sum(safe_float(p.get("revenue")) for p in window)

        working_capital = current_assets - current_liabilities

        x1 = safe_div(working_capital, total_assets)
        x2 = safe_div(retained, total_assets)
        x3 = safe_div(ebit_ttm, total_assets)
        x4 = safe_div(market_cap, total_liabilities)
        x5 = safe_div(revenue_ttm, total_assets)

        z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 0.999 * x5

        if z > 2.99:
            zone, desc = "AN TOÀN", "Vùng an toàn — nguy cơ phá sản thấp."
        elif z >= 1.81:
            zone, desc = "CẢNH BÁO", "Vùng xám — cần theo dõi sát cấu trúc nợ."
        else:
            zone, desc = "RỦI RO CAO", "Vùng kiệt quệ tài chính — rủi ro mất khả năng thanh toán."

        return {
            "z_score": rnd(z, 3),
            "zone": zone,
            "description": desc,
            "components": {
                "X1_working_capital_ratio": rnd(x1, 4),
                "X2_retained_earnings_ratio": rnd(x2, 4),
                "X3_ebit_ratio": rnd(x3, 4),
                "X4_market_cap_to_liabilities": rnd(x4, 4),
                "X5_asset_turnover": rnd(x5, 4),
            },
        }

    # ------------------------------------------------------------------
    def market_risk(self, ohlc: list[dict[str, Any]],
                    index_ohlc: list[dict[str, Any]] | None) -> dict[str, Any]:
        closes = [safe_float(r.get("close")) for r in ohlc]
        rets = to_returns(closes)
        if rets.size < 20:
            return {
                "daily_volatility": 0.0, "annual_volatility": 0.0,
                "beta": self.cfg.default_beta, "max_drawdown": 0.0,
                "var_95_daily": 0.0, "sharpe_ratio": 0.0,
                "annual_return": 0.0, "correlation_with_index": 0.0,
            }

        daily_vol = safe_float(np.std(rets, ddof=1))
        annual_vol = daily_vol * np.sqrt(self.cfg.trading_days_per_year)
        annual_return = safe_float(np.mean(rets)) * self.cfg.trading_days_per_year

        beta, corr = self._beta(rets, index_ohlc)

        prices = np.asarray(closes, dtype=float)
        running_max = np.maximum.accumulate(prices)
        drawdown = np.where(running_max > 0, prices / np.where(running_max == 0, 1.0, running_max) - 1.0, 0.0)
        max_dd = safe_float(np.min(drawdown)) if drawdown.size else 0.0

        var_95 = safe_float(np.percentile(rets, 5))
        sharpe = safe_div(annual_return - self.cfg.risk_free_rate, annual_vol)

        return {
            "daily_volatility": rnd(daily_vol, 4),
            "annual_volatility": rnd(annual_vol, 4),
            "annual_return": rnd(annual_return, 4),
            "beta": rnd(beta, 3),
            "correlation_with_index": rnd(corr, 3),
            "max_drawdown": rnd(max_dd, 4),
            "var_95_daily": rnd(var_95, 4),
            "sharpe_ratio": rnd(sharpe, 3),
        }

    def _beta(self, stock_rets: np.ndarray,
              index_ohlc: list[dict[str, Any]] | None) -> tuple[float, float]:
        """Beta = Cov(Rs, Rm) / Var(Rm). Trả về (beta, hệ số tương quan)."""
        if not index_ohlc or len(index_ohlc) < 21:
            return self.cfg.default_beta, 0.0

        index_rets = to_returns([safe_float(r.get("close")) for r in index_ohlc])
        n = min(stock_rets.size, index_rets.size)
        if n < 20:
            return self.cfg.default_beta, 0.0

        s = stock_rets[-n:]
        m = index_rets[-n:]
        var_m = safe_float(np.var(m, ddof=1))
        if var_m == 0:
            return self.cfg.default_beta, 0.0

        cov = safe_float(np.cov(s, m, ddof=1)[0][1])
        beta = safe_div(cov, var_m, default=self.cfg.default_beta)
        denom = safe_float(np.std(s, ddof=1) * np.std(m, ddof=1))
        corr = safe_div(cov, denom, default=0.0)
        return beta, corr

    # ------------------------------------------------------------------
    def analyze(self, financials: dict[str, Any], ohlc: list[dict[str, Any]],
                index_ohlc: list[dict[str, Any]] | None, market_cap: float,
                fundamentals: dict[str, Any] | None = None) -> dict[str, Any]:
        z = self.altman_z_score(financials, market_cap)
        market = self.market_risk(ohlc, index_ohlc)

        fundamentals = fundamentals or {}
        d_e = safe_float(fundamentals.get("debt_to_equity"))
        current_ratio = safe_float(fundamentals.get("current_ratio"))

        flags: list[str] = []
        if z["z_score"] < 1.81:
            flags.append("Altman Z-Score nằm trong vùng kiệt quệ tài chính.")
        if d_e > 1.5:
            flags.append(f"Đòn bẩy cao: Nợ vay/VCSH = {d_e:.2f} lần.")
        if 0 < current_ratio < 1.0:
            flags.append(f"Thanh khoản ngắn hạn yếu: hệ số hiện hành {current_ratio:.2f}.")
        if market["annual_volatility"] > 0.55:
            flags.append(f"Biến động năm rất cao: {market['annual_volatility'] * 100:.1f}%.")
        if market["max_drawdown"] < -0.35:
            flags.append(f"Sụt giảm tối đa {market['max_drawdown'] * 100:.1f}% trong kỳ quan sát.")

        return {
            "altman": z,
            "market": market,
            "debt_to_equity": rnd(d_e, 4),
            "current_ratio": rnd(current_ratio, 4),
            "risk_flags": flags,
        }
