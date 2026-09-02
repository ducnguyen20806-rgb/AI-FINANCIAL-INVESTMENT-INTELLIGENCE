"""
Module1/mock_source.py
Nguồn dữ liệu mô phỏng (Mock Adapter).

Mục đích: hệ thống chạy được đầy đủ end-to-end khi chưa có consumerID /
consumerSecret của SSI FastConnect. Dữ liệu sinh ra là TẤT ĐỊNH
(deterministic) theo mã cổ phiếu — cùng một mã luôn cho cùng một bộ số,
nhờ vậy có thể kiểm thử và so sánh kết quả giữa các lần chạy.

Cấu trúc dữ liệu trả về giống hệt SSIDataSource để hai adapter thay thế
được cho nhau (Adapter Pattern).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

import numpy as np

TRADING_DAYS = 250
MARKET_SEED = 20240101  # seed cố định cho chuỗi VNINDEX mô phỏng


def market_path(n: int = TRADING_DAYS) -> tuple[np.ndarray, np.ndarray]:
    """Chuỗi shock thị trường và chỉ số VNINDEX mô phỏng (dùng chung mọi mã)."""
    rng = np.random.default_rng(MARKET_SEED)
    shocks = rng.normal(0.00035, 0.0095, n)
    index = 1200.0 * np.exp(np.cumsum(shocks))
    return shocks, index


def _seed_from_symbol(symbol: str) -> int:
    """Sinh seed ổn định từ mã cổ phiếu."""
    digest = hashlib.md5(symbol.upper().encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _business_days(n: int) -> list[datetime]:
    """Sinh n ngày giao dịch gần nhất (bỏ thứ 7, chủ nhật)."""
    days: list[datetime] = []
    cursor = datetime.now()
    while len(days) < n:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(days))


class MockDataSource:
    """Adapter dữ liệu mô phỏng — cùng interface với SSIDataSource."""

    source_name = "MOCK"

    # ------------------------------------------------------------------
    def _rng(self, symbol: str) -> np.random.Generator:
        return np.random.default_rng(_seed_from_symbol(symbol))

    def _price_series(self, symbol: str) -> tuple[list[datetime], np.ndarray, np.ndarray]:
        """
        Sinh chuỗi giá cổ phiếu theo mô hình một nhân tố:

            R_stock = mu + beta * R_market + epsilon

        Chuỗi R_market dùng chung một seed cố định cho MỌI mã, nhờ vậy Beta
        và hệ số tương quan tính ở Module 5 phản ánh đúng quan hệ đã cài đặt.
        """
        rng = self._rng(symbol)
        n = TRADING_DAYS
        market_shock, index = market_path(n)

        base_price = float(rng.integers(12, 120)) * 1000.0  # 12k - 120k VNĐ
        mu = float(rng.uniform(-0.0004, 0.0010))            # drift ngày
        sigma = float(rng.uniform(0.010, 0.022))            # biến động riêng
        beta_true = float(rng.uniform(0.6, 1.6))

        idio_shock = rng.normal(0.0, sigma, n)
        stock_ret = mu + beta_true * market_shock + idio_shock

        prices = base_price * np.exp(np.cumsum(stock_ret))
        return _business_days(n), prices, index

    # ------------------------------------------------------------------
    def get_ohlc(self, symbol: str, start: str | None = None,
                 end: str | None = None, interval: str = "1D") -> list[dict[str, Any]]:
        """Chuỗi nến lịch sử OHLCV."""
        dates, prices, _ = self._price_series(symbol)
        rng = self._rng(symbol + "_ohlc")
        rows: list[dict[str, Any]] = []
        for i, (d, close) in enumerate(zip(dates, prices)):
            prev_close = prices[i - 1] if i > 0 else close
            open_ = prev_close * (1 + rng.normal(0, 0.004))
            high = max(open_, close) * (1 + abs(rng.normal(0, 0.006)))
            low = min(open_, close) * (1 - abs(rng.normal(0, 0.006)))
            volume = float(rng.integers(300_000, 6_000_000))
            rows.append(
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "open": round(open_, 0),
                    "high": round(high, 0),
                    "low": round(low, 0),
                    "close": round(float(close), 0),
                    "volume": volume,
                    "value": round(float(close) * volume, 0),
                }
            )
        return rows

    def get_index_ohlc(self, index_code: str = "VNINDEX") -> list[dict[str, Any]]:
        """Chuỗi nến chỉ số thị trường phục vụ tính Beta."""
        _, index = market_path(TRADING_DAYS)
        dates = _business_days(TRADING_DAYS)
        return [
            {"date": d.strftime("%Y-%m-%d"), "close": round(float(v), 2)}
            for d, v in zip(dates, index)
        ]

    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Giá khớp lệnh và các mức giá trần/sàn/tham chiếu."""
        ohlc = self.get_ohlc(symbol)
        last, prev = ohlc[-1], ohlc[-2]
        ref = prev["close"]
        price = last["close"]
        change = price - ref
        # Biên độ HOSE ±7%
        return {
            "symbol": symbol.upper(),
            "price": price,
            "ref_price": ref,
            "ceiling": round(ref * 1.07, 0),
            "floor": round(ref * 0.93, 0),
            "open": last["open"],
            "high": last["high"],
            "low": last["low"],
            "change": round(change, 0),
            "change_pct": round(change / ref * 100, 2) if ref else 0.0,
            "volume": last["volume"],
            "value": last["value"],
            "trading_date": last["date"],
            "exchange": "HOSE",
        }

    # ------------------------------------------------------------------
    def get_financial_ratios(self, symbol: str) -> dict[str, Any]:
        """
        Báo cáo tài chính mô phỏng: 12 quý gần nhất (3 năm liên tiếp).

        Cách hiệu chỉnh: neo quy mô lợi nhuận theo một mức P/E mục tiêu và
        vốn chủ sở hữu theo một mức P/B mục tiêu, nhờ đó ROE, P/E, P/B của
        dữ liệu mô phỏng luôn nằm trong vùng hợp lý của thị trường Việt Nam.
        """
        rng = self._rng(symbol + "_fin")
        quote = self.get_quote(symbol)
        price = quote["price"]

        shares = float(rng.integers(80, 1500)) * 1_000_000  # 80tr - 1.5 tỷ CP
        market_cap = price * shares

        target_pe = float(rng.uniform(9.0, 19.0))
        target_pb = float(rng.uniform(1.1, 3.5))
        net_margin = float(rng.uniform(0.04, 0.20))
        ebit_margin = net_margin * float(rng.uniform(1.20, 1.75))
        gross_margin = ebit_margin + float(rng.uniform(0.05, 0.20))
        growth_q = float(rng.uniform(0.005, 0.045))   # tăng trưởng quý (2% - 19%/năm)

        net_income_ttm = market_cap / target_pe
        revenue_ttm = net_income_ttm / net_margin
        equity = market_cap / target_pb

        total_assets = equity * float(rng.uniform(1.3, 2.4))
        total_liabilities = total_assets - equity
        short_debt = total_liabilities * float(rng.uniform(0.12, 0.32))
        long_debt = total_liabilities * float(rng.uniform(0.08, 0.24))
        current_assets = total_assets * float(rng.uniform(0.35, 0.65))
        current_liabilities = total_liabilities * float(rng.uniform(0.40, 0.75))
        retained = equity * float(rng.uniform(0.15, 0.55))
        interest_rate = float(rng.uniform(0.055, 0.095))

        periods: list[dict[str, Any]] = []
        now = datetime.now()
        for i in range(12):  # từ quý xa nhất tới quý gần nhất
            k = 11 - i
            quarter_dt = now - timedelta(days=90 * k)
            factor = (1 + growth_q) ** (-k)
            noise = float(rng.uniform(0.94, 1.06))

            rev = revenue_ttm / 4 * factor * noise
            ni = rev * net_margin
            ebit = rev * ebit_margin
            gross = rev * gross_margin
            cfo = ni * float(rng.uniform(1.00, 1.50))
            capex = cfo * float(rng.uniform(0.15, 0.45))
            interest = (short_debt + long_debt) * factor * interest_rate / 4

            periods.append(
                {
                    "period": f"{quarter_dt.year}Q{(quarter_dt.month - 1) // 3 + 1}",
                    "revenue": round(rev, 0),
                    "gross_profit": round(gross, 0),
                    "ebit": round(ebit, 0),
                    "net_income": round(ni, 0),
                    "cfo": round(cfo, 0),
                    "capex": round(capex, 0),
                    "total_assets": round(total_assets * factor, 0),
                    "current_assets": round(current_assets * factor, 0),
                    "current_liabilities": round(current_liabilities * factor, 0),
                    "total_liabilities": round(total_liabilities * factor, 0),
                    "equity": round(equity * factor, 0),
                    "retained_earnings": round(retained * factor, 0),
                    "short_debt": round(short_debt * factor, 0),
                    "long_debt": round(long_debt * factor, 0),
                    "interest_expense": round(interest, 0),
                    "cash": round(total_assets * factor * 0.08, 0),
                }
            )

        return {
            "periods": periods,
            "shares_outstanding": shares,
            "sector": "Mô phỏng",
            "peers": {
                "pe": round(target_pe * float(rng.uniform(0.85, 1.20)), 2),
                "pb": round(target_pb * float(rng.uniform(0.85, 1.20)), 2),
                "roe": round(target_pb / target_pe, 4),
            },
        }

    # ------------------------------------------------------------------
    def get_all_stock_data(self, symbol: str) -> dict[str, Any]:
        """Orchestrator: gom toàn bộ dữ liệu của một mã trong một lần gọi."""
        symbol = symbol.upper().strip()
        return {
            "symbol": symbol,
            "source": self.source_name,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "quote": self.get_quote(symbol),
            "ohlc": self.get_ohlc(symbol),
            "index_ohlc": self.get_index_ohlc(),
            "financials": self.get_financial_ratios(symbol),
            "warnings": ["Đang dùng dữ liệu MÔ PHỎNG — chưa cấu hình SSI FastConnect."],
        }
