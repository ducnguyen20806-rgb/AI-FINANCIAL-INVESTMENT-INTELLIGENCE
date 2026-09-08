"""
Module2/fundamental_engine.py
FUNDAMENTAL ENGINE — Bóc tách sức khoẻ tài chính doanh nghiệp.

Đầu vào: khối "financials" do Module 1 chuẩn hoá (danh sách kỳ báo cáo,
sắp xếp từ kỳ xa nhất đến kỳ gần nhất).

Đầu ra: bộ chỉ tiêu TTM (4 quý gần nhất) + chuỗi tăng trưởng nhiều năm:
    - Biên lợi nhuận gộp, biên EBIT, biên lợi nhuận ròng
    - Tỷ lệ CFO / Net Income (độ trung thực của lợi nhuận)
    - Đòn bẩy tài chính Debt/Equity, hệ số thanh toán hiện hành
    - ROE, ROA, ROIC
    - CAGR doanh thu & lợi nhuận
    - Free Cash Flow = CFO - Capex
"""
from __future__ import annotations

from typing import Any

from common.utils import cagr, rnd, safe_div, safe_float


class FundamentalEngine:
    """Engine phân tích cơ bản."""

    TTM_QUARTERS = 4

    # ------------------------------------------------------------------
    def analyze(self, financials: dict[str, Any]) -> dict[str, Any]:
        periods: list[dict[str, Any]] = list(financials.get("periods") or [])
        if not periods:
            return self._empty()

        latest = periods[-1]
        ttm = self._sum_ttm(periods)

        revenue = ttm["revenue"]
        gross_profit = ttm["gross_profit"]
        ebit = ttm["ebit"]
        net_income = ttm["net_income"]
        cfo = ttm["cfo"]
        capex = ttm["capex"]

        equity = safe_float(latest.get("equity"))
        total_assets = safe_float(latest.get("total_assets"))
        total_liabilities = safe_float(latest.get("total_liabilities"))
        short_debt = safe_float(latest.get("short_debt"))
        long_debt = safe_float(latest.get("long_debt"))
        total_debt = short_debt + long_debt
        current_assets = safe_float(latest.get("current_assets"))
        current_liabilities = safe_float(latest.get("current_liabilities"))
        tax_rate = 0.20

        # Vốn đầu tư = Nợ vay + Vốn chủ sở hữu
        invested_capital = total_debt + equity
        nopat = ebit * (1 - tax_rate)

        result = {
            # --- Biên lợi nhuận ---
            "gross_margin": rnd(safe_div(gross_profit, revenue), 4),
            "ebit_margin": rnd(safe_div(ebit, revenue), 4),
            "net_margin": rnd(safe_div(net_income, revenue), 4),
            # --- Chất lượng lợi nhuận ---
            "cfo_to_net_income": rnd(safe_div(cfo, net_income), 4),
            "free_cash_flow": rnd(cfo - capex, 0),
            "fcf_margin": rnd(safe_div(cfo - capex, revenue), 4),
            # --- Hiệu quả sử dụng vốn ---
            "roe": rnd(safe_div(net_income, equity), 4),
            "roa": rnd(safe_div(net_income, total_assets), 4),
            "roic": rnd(safe_div(nopat, invested_capital), 4),
            # --- Đòn bẩy & thanh khoản ---
            "debt_to_equity": rnd(safe_div(total_debt, equity), 4),
            "liabilities_to_equity": rnd(safe_div(total_liabilities, equity), 4),
            "current_ratio": rnd(safe_div(current_assets, current_liabilities), 4),
            "interest_coverage": rnd(safe_div(ebit, ttm["interest_expense"]), 2),
            # --- Quy mô TTM ---
            "revenue_ttm": rnd(revenue, 0),
            "ebit_ttm": rnd(ebit, 0),
            "net_income_ttm": rnd(net_income, 0),
            "cfo_ttm": rnd(cfo, 0),
            "capex_ttm": rnd(capex, 0),
            "equity": rnd(equity, 0),
            "total_assets": rnd(total_assets, 0),
            "total_debt": rnd(total_debt, 0),
            "eps_ttm": 0.0,  # được điền ở Module 3 khi biết số CP lưu hành
            "book_value": rnd(equity, 0),
            "latest_period": latest.get("period", ""),
        }

        result.update(self._growth(periods))
        result["piotroski_f_score"] = self._piotroski_f_score(periods)
        result["history"] = self._history(periods)
        return result

    # ------------------------------------------------------------------
    def _sum_ttm(self, periods: list[dict[str, Any]]) -> dict[str, float]:
        """Cộng dồn các khoản mục kết quả kinh doanh của 4 quý gần nhất."""
        window = periods[-self.TTM_QUARTERS:]
        keys = ["revenue", "gross_profit", "ebit", "net_income", "cfo", "capex", "interest_expense"]
        return {k: sum(safe_float(p.get(k)) for p in window) for k in keys}

    def _growth(self, periods: list[dict[str, Any]]) -> dict[str, float]:
        """Tăng trưởng YoY quý gần nhất và CAGR theo số kỳ có sẵn."""
        out = {"revenue_growth_yoy": 0.0, "net_income_growth_yoy": 0.0,
               "revenue_cagr": 0.0, "net_income_cagr": 0.0, "cagr_years": 0.0}

        if len(periods) >= 5:
            cur, prev = periods[-1], periods[-5]
            out["revenue_growth_yoy"] = rnd(
                safe_div(safe_float(cur.get("revenue")) - safe_float(prev.get("revenue")),
                         abs(safe_float(prev.get("revenue")))), 4)
            out["net_income_growth_yoy"] = rnd(
                safe_div(safe_float(cur.get("net_income")) - safe_float(prev.get("net_income")),
                         abs(safe_float(prev.get("net_income")))), 4)

        if len(periods) >= 8:
            years = len(periods) / 4.0 - 1.0
            first_year = sum(safe_float(p.get("revenue")) for p in periods[:4])
            last_year = sum(safe_float(p.get("revenue")) for p in periods[-4:])
            out["revenue_cagr"] = rnd(cagr(first_year, last_year, years), 4)

            first_ni = sum(safe_float(p.get("net_income")) for p in periods[:4])
            last_ni = sum(safe_float(p.get("net_income")) for p in periods[-4:])
            out["net_income_cagr"] = rnd(cagr(first_ni, last_ni, years), 4)
            out["cagr_years"] = rnd(years, 2)

        return out

    def _history(self, periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Chuỗi lịch sử để vẽ biểu đồ ở tầng giao diện."""
        rows = []
        for p in periods:
            revenue = safe_float(p.get("revenue"))
            rows.append(
                {
                    "period": p.get("period", ""),
                    "revenue": rnd(revenue, 0),
                    "ebit": rnd(safe_float(p.get("ebit")), 0),
                    "net_income": rnd(safe_float(p.get("net_income")), 0),
                    "cfo": rnd(safe_float(p.get("cfo")), 0),
                    "net_margin": rnd(safe_div(p.get("net_income"), revenue), 4),
                    "ebit_margin": rnd(safe_div(p.get("ebit"), revenue), 4),
                }
            )
        return rows

    def _piotroski_f_score(self, periods: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Piotroski F-Score (thang điểm 0 - 9 đánh giá sức mạnh tài chính kế toán):
        - Nhóm Sinh lời (Profitability): ROA > 0, CFO > 0, delta ROA > 0, CFO > Net Income
        - Nhóm Đòn bẩy & Thanh khoản (Leverage): delta Nợ dài hạn <= 0, delta Current Ratio >= 0, Không pha loãng CP
        - Nhóm Hiệu quả (Efficiency): delta Biên gộp >= 0, delta Vòng quay tài sản >= 0
        """
        if not periods:
            return {"score": 0, "rating": "KHÔNG XÁC ĐỊNH", "criteria": {}}

        latest = periods[-1]
        prev_year = periods[-5] if len(periods) >= 5 else (periods[0] if len(periods) > 1 else latest)

        ttm_cur = self._sum_ttm(periods)
        ttm_prev = self._sum_ttm(periods[:-4]) if len(periods) >= 8 else ttm_cur

        ni_cur = ttm_cur["net_income"]
        cfo_cur = ttm_cur["cfo"]
        assets_cur = max(safe_float(latest.get("total_assets")), 1.0)
        assets_prev = max(safe_float(prev_year.get("total_assets")), 1.0)

        roa_cur = safe_div(ni_cur, assets_cur)
        roa_prev = safe_div(ttm_prev["net_income"], assets_prev)

        # 1. ROA dương
        f1 = roa_cur > 0
        # 2. CFO dương
        f2 = cfo_cur > 0
        # 3. ROA tăng trưởng
        f3 = roa_cur > roa_prev
        # 4. CFO > Net Income (Accrual quality)
        f4 = cfo_cur > ni_cur

        # 5. Đòn bẩy giảm (Long-term debt / Assets)
        lev_cur = safe_div(safe_float(latest.get("long_debt")), assets_cur)
        lev_prev = safe_div(safe_float(prev_year.get("long_debt")), assets_prev)
        f5 = lev_cur <= lev_prev

        # 6. Khả năng thanh toán hiện hành tăng
        cr_cur = safe_div(safe_float(latest.get("current_assets")), max(safe_float(latest.get("current_liabilities")), 1.0))
        cr_prev = safe_div(safe_float(prev_year.get("current_assets")), max(safe_float(prev_year.get("current_liabilities")), 1.0))
        f6 = cr_cur >= cr_prev

        # 7. Số lượng cổ phiếu không tăng pha loãng
        shares_cur = safe_float(latest.get("shares_outstanding"))
        shares_prev = safe_float(prev_year.get("shares_outstanding"))
        f7 = (shares_cur <= shares_prev) if (shares_cur > 0 and shares_prev > 0) else True

        # 8. Biên gộp tăng
        gm_cur = safe_div(ttm_cur["gross_profit"], max(ttm_cur["revenue"], 1.0))
        gm_prev = safe_div(ttm_prev["gross_profit"], max(ttm_prev["revenue"], 1.0))
        f8 = gm_cur >= gm_prev

        # 9. Vòng quay tài sản tăng
        at_cur = safe_div(ttm_cur["revenue"], assets_cur)
        at_prev = safe_div(ttm_prev["revenue"], assets_prev)
        f9 = at_cur >= at_prev

        criteria = {
            "roa_positive": f1,
            "cfo_positive": f2,
            "roa_growth": f3,
            "accrual_cfo_gt_ni": f4,
            "leverage_decreased": f5,
            "liquidity_improved": f6,
            "no_share_dilution": f7,
            "gross_margin_improved": f8,
            "asset_turnover_improved": f9,
        }
        score = sum(1 for passed in criteria.values() if passed)

        if score >= 8:
            rating = "RẤT MẠNH (8-9)"
        elif score >= 5:
            rating = "ỔN ĐỊNH (5-7)"
        else:
            rating = "YẾU KÉM (0-4)"

        return {
            "score": score,
            "rating": rating,
            "criteria": criteria,
        }

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {
            "gross_margin": 0.0, "ebit_margin": 0.0, "net_margin": 0.0,
            "cfo_to_net_income": 0.0, "free_cash_flow": 0.0, "fcf_margin": 0.0,
            "roe": 0.0, "roa": 0.0, "roic": 0.0,
            "debt_to_equity": 0.0, "liabilities_to_equity": 0.0,
            "current_ratio": 0.0, "interest_coverage": 0.0,
            "revenue_ttm": 0.0, "ebit_ttm": 0.0, "net_income_ttm": 0.0,
            "cfo_ttm": 0.0, "capex_ttm": 0.0, "equity": 0.0, "total_assets": 0.0,
            "total_debt": 0.0, "eps_ttm": 0.0, "book_value": 0.0,
            "latest_period": "", "revenue_growth_yoy": 0.0,
            "net_income_growth_yoy": 0.0, "revenue_cagr": 0.0,
            "net_income_cagr": 0.0, "cagr_years": 0.0, "history": [],
            "piotroski_f_score": {"score": 0, "rating": "KHÔNG XÁC ĐỊNH", "criteria": {}},
            "error": "Không có dữ liệu báo cáo tài chính.",
        }
