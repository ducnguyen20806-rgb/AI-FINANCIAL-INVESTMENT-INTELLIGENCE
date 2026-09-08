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

from common.utils import clamp, rnd, safe_div, safe_float, to_returns
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
    def beneish_m_score(self, financials: dict[str, Any]) -> dict[str, Any]:
        """
        Beneish M-Score (Mô hình phát hiện gian lận báo cáo tài chính):
        M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.037*TATA + 0.0327*LVGI
        Ngưỡng: M > -1.78 -> Nguy cơ thao túng BCTC cao
        """
        periods = financials.get("periods") or []
        if len(periods) < 5:
            return {
                "m_score": -2.5,
                "manipulation_risk": "THẤP",
                "description": "Không đủ kỳ so sánh (cần tối thiểu 5 quý), tạm ước tính an toàn.",
                "components": {},
            }

        cur = periods[-1]
        prev = periods[-5] if len(periods) >= 5 else periods[0]

        sales_t = max(safe_float(cur.get("revenue")), 1.0)
        sales_t1 = max(safe_float(prev.get("revenue")), 1.0)

        rec_t = safe_float(cur.get("receivables"), safe_float(cur.get("current_assets")) * 0.3)
        rec_t1 = safe_float(prev.get("receivables"), safe_float(prev.get("current_assets")) * 0.3)

        dsri = safe_div(safe_div(rec_t, sales_t), max(safe_div(rec_t1, sales_t1), 1e-6), default=1.0)

        gp_t = safe_float(cur.get("gross_profit"))
        gp_t1 = safe_float(prev.get("gross_profit"))
        gm_t = safe_div(gp_t, sales_t)
        gm_t1 = safe_div(gp_t1, sales_t1)
        gmi = safe_div(gm_t1, max(gm_t, 1e-6), default=1.0)

        assets_t = max(safe_float(cur.get("total_assets")), 1.0)
        assets_t1 = max(safe_float(prev.get("total_assets")), 1.0)
        ppe_t = safe_float(cur.get("fixed_assets"), assets_t * 0.4)
        ppe_t1 = safe_float(prev.get("fixed_assets"), assets_t1 * 0.4)
        ca_t = safe_float(cur.get("current_assets"))
        ca_t1 = safe_float(prev.get("current_assets"))

        aq_t = 1.0 - safe_div(ca_t + ppe_t, assets_t)
        aq_t1 = 1.0 - safe_div(ca_t1 + ppe_t1, assets_t1)
        aqi = safe_div(aq_t, max(aq_t1, 1e-6), default=1.0)

        sgi = safe_div(sales_t, sales_t1, default=1.0)

        depi = 1.0
        sgai = 1.0

        debt_t = safe_float(cur.get("short_debt")) + safe_float(cur.get("long_debt"))
        debt_t1 = safe_float(prev.get("short_debt")) + safe_float(prev.get("long_debt"))
        lvgi = safe_div(safe_div(debt_t, assets_t), max(safe_div(debt_t1, assets_t1), 1e-6), default=1.0)

        cfo_t = safe_float(cur.get("cfo"))
        ni_t = safe_float(cur.get("net_income"))
        tata = safe_div(ni_t - cfo_t, assets_t)

        dsri = clamp(dsri, 0.5, 3.0)
        gmi = clamp(gmi, 0.5, 3.0)
        aqi = clamp(aqi, 0.5, 3.0)
        sgi = clamp(sgi, 0.5, 3.0)
        lvgi = clamp(lvgi, 0.5, 3.0)
        tata = clamp(tata, -1.0, 1.0)

        m = -4.84 + 0.920 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi + 0.115 * depi - 0.172 * sgai + 4.037 * tata + 0.0327 * lvgi

        if m > -1.78:
            risk_level = "NGUY CƠ CAO"
            desc = "Beneish M-Score > -1.78: Tín hiệu cảnh báo nguy cơ thao túng lợi nhuận kế toán."
        else:
            risk_level = "AN TOÀN"
            desc = "Beneish M-Score <= -1.78: Xác suất thao túng số liệu BCTC ở mức thấp."

        return {
            "m_score": rnd(m, 3),
            "manipulation_risk": risk_level,
            "description": desc,
            "components": {
                "DSRI_receivables": rnd(dsri, 3),
                "GMI_gross_margin": rnd(gmi, 3),
                "AQI_asset_quality": rnd(aqi, 3),
                "SGI_sales_growth": rnd(sgi, 3),
                "DEPI_depreciation": rnd(depi, 3),
                "SGAI_sga_expense": rnd(sgai, 3),
                "LVGI_leverage": rnd(lvgi, 3),
                "TATA_accruals": rnd(tata, 3),
            },
        }

    # ------------------------------------------------------------------
    @staticmethod
    def optimize_portfolio(returns_dict: dict[str, list[float]],
                           risk_free_rate: float = 0.03,
                           num_simulations: int = 1000) -> dict[str, Any]:
        """
        Tối ưu hóa danh mục đầu tư đa mã theo Markowitz Modern Portfolio Theory:
        - Sinh ngẫu nhiên N danh mục (Monte Carlo simulation)
        - Tìm danh mục Sharpe Ratio tối đa và Biến động rủi ro tối thiểu
        """
        symbols = list(returns_dict.keys())
        if len(symbols) < 2:
            return {"error": "Cần tối thiểu 2 mã cổ phiếu để tối ưu danh mục."}

        min_len = min(len(r) for r in returns_dict.values())
        if min_len < 10:
            return {"error": "Chuỗi dữ liệu giá quá ngắn để tính hiệp phương sai."}

        ret_matrix = np.array([returns_dict[s][-min_len:] for s in symbols])
        mean_daily = np.mean(ret_matrix, axis=1)
        mean_annual = mean_daily * 250
        cov_daily = np.cov(ret_matrix)
        cov_annual = cov_daily * 250

        n_assets = len(symbols)
        rng = np.random.default_rng(42)

        results = np.zeros((3, num_simulations))
        all_weights = np.zeros((num_simulations, n_assets))

        for i in range(num_simulations):
            w = rng.random(n_assets)
            w = w / np.sum(w)
            all_weights[i, :] = w

            p_ret = np.sum(w * mean_annual)
            p_vol = np.sqrt(np.dot(w.T, np.dot(cov_annual, w)))
            p_sharpe = (p_ret - risk_free_rate) / p_vol if p_vol > 0 else 0.0

            results[0, i] = p_ret
            results[1, i] = p_vol
            results[2, i] = p_sharpe

        max_sharpe_idx = int(np.argmax(results[2]))
        max_sharpe_weights = {symbols[j]: rnd(float(all_weights[max_sharpe_idx, j]), 4) for j in range(n_assets)}

        min_vol_idx = int(np.argmin(results[1]))
        min_vol_weights = {symbols[j]: rnd(float(all_weights[min_vol_idx, j]), 4) for j in range(n_assets)}

        corr_matrix = np.corrcoef(ret_matrix).tolist()

        return {
            "symbols": symbols,
            "correlation_matrix": [[rnd(c, 3) for c in row] for row in corr_matrix],
            "max_sharpe": {
                "return": rnd(float(results[0, max_sharpe_idx]), 4),
                "volatility": rnd(float(results[1, max_sharpe_idx]), 4),
                "sharpe": rnd(float(results[2, max_sharpe_idx]), 3),
                "weights": max_sharpe_weights,
            },
            "min_volatility": {
                "return": rnd(float(results[0, min_vol_idx]), 4),
                "volatility": rnd(float(results[1, min_vol_idx]), 4),
                "sharpe": rnd(float(results[2, min_vol_idx]), 3),
                "weights": min_vol_weights,
            },
            "sample_points": [
                {
                    "return": rnd(float(results[0, i]), 4),
                    "volatility": rnd(float(results[1, i]), 4),
                    "sharpe": rnd(float(results[2, i]), 3),
                }
                for i in range(0, min(num_simulations, 250), 2)
            ],
        }

    # ------------------------------------------------------------------
    def analyze(self, financials: dict[str, Any], ohlc: list[dict[str, Any]],
                index_ohlc: list[dict[str, Any]] | None, market_cap: float,
                fundamentals: dict[str, Any] | None = None) -> dict[str, Any]:
        z = self.altman_z_score(financials, market_cap)
        beneish = self.beneish_m_score(financials)
        market = self.market_risk(ohlc, index_ohlc)

        fundamentals = fundamentals or {}
        d_e = safe_float(fundamentals.get("debt_to_equity"))
        current_ratio = safe_float(fundamentals.get("current_ratio"))

        flags: list[str] = []
        if z["z_score"] < 1.81:
            flags.append("Altman Z-Score nằm trong vùng kiệt quệ tài chính.")
        if beneish["m_score"] > -1.78:
            flags.append(f"Beneish M-Score cảnh báo nguy cơ thao túng BCTC: M = {beneish['m_score']:.2f} > -1.78.")
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
            "beneish": beneish,
            "market": market,
            "debt_to_equity": rnd(d_e, 4),
            "current_ratio": rnd(current_ratio, 4),
            "risk_flags": flags,
        }
