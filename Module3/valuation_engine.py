"""
Module3/valuation_engine.py
VALUATION ENGINE — Định giá nội tại (DCF) và định giá so sánh (Multiples).

Mô hình DCF nhiều giai đoạn:

                 5      FCF_t            Terminal Value
    EV  =       SUM  ------------   +   ----------------
                t=1  (1 + WACC)^t         (1 + WACC)^5

    Terminal Value = FCF_5 * (1 + g) / (WACC - g),  g = 3% (mặc định)

    Intrinsic Value / CP = (EV - Nợ thuần) / Số CP lưu hành

WACC = E/(D+E) * Re + D/(D+E) * Rd * (1 - t)
    Re (CAPM) = Rf + Beta * ERP
    Rd        = Chi phí lãi vay / Tổng nợ vay
"""
from __future__ import annotations

from typing import Any

from common.utils import clamp, rnd, safe_div, safe_float
from config import finance_config


class ValuationEngine:
    """Engine định giá."""

    def __init__(self, config=finance_config) -> None:
        self.cfg = config

    # ------------------------------------------------------------------
    # WACC
    # ------------------------------------------------------------------
    def compute_wacc(self, fundamentals: dict[str, Any], market_cap: float,
                     beta: float) -> dict[str, Any]:
        equity_value = max(market_cap, 1.0)
        total_debt = safe_float(fundamentals.get("total_debt"))

        # Chi phí nợ vay: lãi vay TTM / tổng nợ vay; chặn trong [3%, 15%]
        ebit = safe_float(fundamentals.get("ebit_ttm"))
        coverage = safe_float(fundamentals.get("interest_coverage"))
        implied_interest = safe_div(ebit, coverage) if coverage > 0 else 0.0
        cost_of_debt = safe_div(implied_interest, total_debt, default=0.08)
        cost_of_debt = clamp(cost_of_debt, 0.03, 0.15)

        beta = clamp(beta if beta else self.cfg.default_beta, 0.3, 2.5)
        cost_of_equity = self.cfg.risk_free_rate + beta * self.cfg.equity_risk_premium

        v = equity_value + total_debt
        we = safe_div(equity_value, v, default=1.0)
        wd = safe_div(total_debt, v, default=0.0)

        wacc = we * cost_of_equity + wd * cost_of_debt * (1 - self.cfg.corporate_tax_rate)
        # WACC phải lớn hơn g để Terminal Value có nghĩa
        wacc = clamp(wacc, self.cfg.terminal_growth + 0.02, 0.30)

        return {
            "wacc": rnd(wacc, 4),
            "cost_of_equity": rnd(cost_of_equity, 4),
            "cost_of_debt": rnd(cost_of_debt, 4),
            "weight_equity": rnd(we, 4),
            "weight_debt": rnd(wd, 4),
            "beta_used": rnd(beta, 3),
            "risk_free_rate": self.cfg.risk_free_rate,
            "equity_risk_premium": self.cfg.equity_risk_premium,
            "tax_rate": self.cfg.corporate_tax_rate,
        }

    # ------------------------------------------------------------------
    # DCF
    # ------------------------------------------------------------------
    def discounted_cash_flow(self, fcf_base: float, wacc: float, growth: float,
                             net_debt: float, shares: float) -> dict[str, Any]:
        g_terminal = self.cfg.terminal_growth
        years = self.cfg.forecast_years

        # Tốc độ tăng trưởng giai đoạn dự báo: chặn trong [-5%, +20%]
        # và không vượt quá WACC + 8% để Terminal Value không bị thổi phồng.
        g = clamp(growth, -0.05, min(0.20, wacc + 0.08))

        if fcf_base <= 0:
            return {
                "intrinsic_value_per_share": 0.0,
                "enterprise_value": 0.0,
                "equity_value": 0.0,
                "terminal_value": 0.0,
                "pv_terminal": 0.0,
                "projection": [],
                "growth_used": rnd(g, 4),
                "note": "FCF cơ sở âm hoặc bằng 0 — mô hình DCF không áp dụng được.",
            }

        projection: list[dict[str, Any]] = []
        pv_sum = 0.0
        fcf_t = fcf_base
        for t in range(1, years + 1):
            fcf_t = fcf_t * (1 + g)
            discount = (1 + wacc) ** t
            pv = fcf_t / discount
            pv_sum += pv
            projection.append(
                {"year": t, "fcf": rnd(fcf_t, 0), "discount_factor": rnd(1 / discount, 4),
                 "present_value": rnd(pv, 0)}
            )

        terminal_value = fcf_t * (1 + g_terminal) / (wacc - g_terminal)
        pv_terminal = terminal_value / ((1 + wacc) ** years)

        enterprise_value = pv_sum + pv_terminal
        equity_value = enterprise_value - net_debt
        per_share = safe_div(equity_value, shares)

        return {
            "intrinsic_value_per_share": rnd(max(per_share, 0.0), 0),
            "enterprise_value": rnd(enterprise_value, 0),
            "equity_value": rnd(equity_value, 0),
            "terminal_value": rnd(terminal_value, 0),
            "pv_terminal": rnd(pv_terminal, 0),
            "pv_explicit": rnd(pv_sum, 0),
            "projection": projection,
            "growth_used": rnd(g, 4),
            "terminal_growth": g_terminal,
            "note": "",
        }

    # ------------------------------------------------------------------
    def sensitivity_matrix(self, fcf_base: float, base_wacc: float, growth: float,
                           net_debt: float, shares: float) -> dict[str, Any]:
        """
        Ma trận phân tích độ nhạy DCF 2 chiều: WACC vs Terminal Growth g.
        """
        years = self.cfg.forecast_years
        g = clamp(growth, -0.05, 0.20)

        wacc_steps = [base_wacc - 0.02, base_wacc - 0.01, base_wacc, base_wacc + 0.01, base_wacc + 0.02]
        wacc_steps = [clamp(w, 0.06, 0.30) for w in wacc_steps]
        wacc_labels = [f"{w * 100:.1f}%" for w in wacc_steps]

        g_steps = [0.015, 0.020, 0.025, 0.030, 0.035, 0.040]
        g_labels = [f"{gv * 100:.1f}%" for gv in g_steps]

        matrix: list[list[float]] = []
        for w_val in wacc_steps:
            row: list[float] = []
            for g_term in g_steps:
                if fcf_base <= 0 or w_val <= g_term:
                    row.append(0.0)
                    continue

                pv_sum = 0.0
                fcf_t = fcf_base
                for t in range(1, years + 1):
                    fcf_t = fcf_t * (1 + g)
                    discount = (1 + w_val) ** t
                    pv_sum += fcf_t / discount

                tv = fcf_t * (1 + g_term) / (w_val - g_term)
                pv_tv = tv / ((1 + w_val) ** years)

                ev = pv_sum + pv_tv
                eq = ev - net_debt
                val_per_share = max(safe_div(eq, shares), 0.0)
                row.append(rnd(val_per_share, 0))
            matrix.append(row)

        return {
            "wacc_labels": wacc_labels,
            "g_labels": g_labels,
            "matrix": matrix,
            "base_wacc": rnd(base_wacc, 4),
            "base_growth": rnd(g, 4),
        }

    # ------------------------------------------------------------------
    # Orchestrator của Module 3
    # ------------------------------------------------------------------
    def analyze(self, fundamentals: dict[str, Any], quote: dict[str, Any],
                financials: dict[str, Any], beta: float = 1.0) -> dict[str, Any]:
        price = safe_float(quote.get("price"))
        shares = safe_float(financials.get("shares_outstanding"))
        if shares <= 0:
            # Suy ra số CP từ vốn chủ sở hữu nếu nguồn không cung cấp
            shares = max(safe_div(fundamentals.get("equity"), max(price, 1.0)), 1.0)

        market_cap = price * shares
        net_income = safe_float(fundamentals.get("net_income_ttm"))
        equity = safe_float(fundamentals.get("equity"))
        eps = safe_div(net_income, shares)
        bvps = safe_div(equity, shares)

        wacc_block = self.compute_wacc(fundamentals, market_cap, beta)
        wacc = wacc_block["wacc"]

        fcf = safe_float(fundamentals.get("free_cash_flow"))
        growth = safe_float(fundamentals.get("revenue_cagr")) or safe_float(
            fundamentals.get("revenue_growth_yoy")
        )
        latest = (financials.get("periods") or [{}])[-1]
        net_debt = (safe_float(latest.get("short_debt")) + safe_float(latest.get("long_debt"))
                    - safe_float(latest.get("cash")))

        dcf = self.discounted_cash_flow(fcf, wacc, growth, net_debt, shares)
        intrinsic = dcf["intrinsic_value_per_share"]
        sensitivity = self.sensitivity_matrix(fcf, wacc, growth, net_debt, shares)

        pe = safe_div(price, eps)
        pb = safe_div(price, bvps)
        peers = financials.get("peers") or {}
        peer_pe = safe_float(peers.get("pe"))
        peer_pb = safe_float(peers.get("pb"))

        # Định giá so sánh: giá mục tiêu theo bội số ngành
        target_by_pe = peer_pe * eps if peer_pe > 0 else 0.0
        target_by_pb = peer_pb * bvps if peer_pb > 0 else 0.0
        relative_targets = [t for t in (target_by_pe, target_by_pb) if t > 0]
        relative_value = sum(relative_targets) / len(relative_targets) if relative_targets else 0.0

        if intrinsic > 0 and relative_value > 0:
            fair_value = intrinsic * 0.60 + relative_value * 0.40
        elif intrinsic > 0:
            fair_value = intrinsic
        elif relative_value > 0:
            fair_value = relative_value
        else:
            fair_value = price

        upside = safe_div(fair_value - price, price) if price else 0.0

        return {
            "price": rnd(price, 0),
            "shares_outstanding": rnd(shares, 0),
            "market_cap": rnd(market_cap, 0),
            "eps": rnd(eps, 2),
            "bvps": rnd(bvps, 2),
            "pe": rnd(pe, 2),
            "pb": rnd(pb, 2),
            "peer_pe": rnd(peer_pe, 2),
            "peer_pb": rnd(peer_pb, 2),
            "pe_discount_vs_peer": rnd(safe_div(pe - peer_pe, peer_pe), 4) if peer_pe else 0.0,
            "intrinsic_value": intrinsic,
            "relative_value": rnd(relative_value, 0),
            "fair_value": rnd(fair_value, 0),
            "upside": rnd(upside, 4),
            "fair_buy_price": rnd(fair_value * 0.85, 0),  # biên an toàn 15%
            "net_debt": rnd(net_debt, 0),
            "wacc_detail": wacc_block,
            "wacc": wacc,
            "dcf": dcf,
            "sensitivity": sensitivity,
        }
