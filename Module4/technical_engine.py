"""
Module4/technical_engine.py
TECHNICAL & MOMENTUM ENGINE

Tính toán trực tiếp trên chuỗi nến OHLC do Module 1 cung cấp, không phụ
thuộc thư viện TA bên ngoài (mọi công thức đều hiện thực bằng NumPy để
kiểm soát chính xác cách làm mượt).

    - EMA20 / EMA50 đệ quy:  EMA_t = alpha*P_t + (1-alpha)*EMA_{t-1}
    - RSI 14 phiên theo phương pháp làm mượt Wilder
    - MACD = EMA12 - EMA26; Signal = EMA9(MACD); Histogram = MACD - Signal
    - Hỗ trợ / Kháng cự: cực trị trong 60 phiên gần nhất
"""
from __future__ import annotations

from typing import Any

import numpy as np

from common.utils import rnd, safe_div, safe_float


class TechnicalEngine:
    """Engine phân tích kỹ thuật."""

    RSI_PERIOD = 14
    SR_WINDOW = 60

    # ------------------------------------------------------------------
    # Các hàm chỉ báo cơ sở
    # ------------------------------------------------------------------
    @staticmethod
    def ema(values: np.ndarray, period: int) -> np.ndarray:
        """EMA đệ quy, khởi tạo bằng SMA của `period` phần tử đầu."""
        n = values.size
        out = np.full(n, np.nan)
        if n < period or period <= 0:
            return out
        alpha = 2.0 / (period + 1.0)
        out[period - 1] = values[:period].mean()
        for i in range(period, n):
            out[i] = alpha * values[i] + (1 - alpha) * out[i - 1]
        return out

    @staticmethod
    def sma(values: np.ndarray, period: int) -> np.ndarray:
        n = values.size
        out = np.full(n, np.nan)
        if n < period:
            return out
        cumsum = np.cumsum(np.insert(values, 0, 0.0))
        out[period - 1:] = (cumsum[period:] - cumsum[:-period]) / period
        return out

    @classmethod
    def wilder_rsi(cls, close: np.ndarray, period: int = 14) -> np.ndarray:
        """RSI theo phương pháp làm mượt Wilder (loại nhiễu tốt hơn SMA)."""
        n = close.size
        out = np.full(n, np.nan)
        if n <= period:
            return out

        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)

        avg_gain = gain[:period].mean()
        avg_loss = loss[:period].mean()
        out[period] = cls._rsi_value(avg_gain, avg_loss)

        for i in range(period, delta.size):
            avg_gain = (avg_gain * (period - 1) + gain[i]) / period
            avg_loss = (avg_loss * (period - 1) + loss[i]) / period
            out[i + 1] = cls._rsi_value(avg_gain, avg_loss)
        return out

    @staticmethod
    def _rsi_value(avg_gain: float, avg_loss: float) -> float:
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @classmethod
    def macd(cls, close: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        ema12 = cls.ema(close, 12)
        ema26 = cls.ema(close, 26)
        macd_line = ema12 - ema26
        valid = macd_line[~np.isnan(macd_line)]
        signal = np.full(close.size, np.nan)
        if valid.size >= 9:
            sig_valid = cls.ema(valid, 9)
            signal[close.size - valid.size:] = sig_valid
        hist = macd_line - signal
        return macd_line, signal, hist

    # ------------------------------------------------------------------
    def analyze(self, ohlc: list[dict[str, Any]]) -> dict[str, Any]:
        if not ohlc or len(ohlc) < 30:
            return self._empty()

        close = np.asarray([safe_float(r.get("close")) for r in ohlc], dtype=float)
        high = np.asarray([safe_float(r.get("high")) for r in ohlc], dtype=float)
        low = np.asarray([safe_float(r.get("low")) for r in ohlc], dtype=float)
        volume = np.asarray([safe_float(r.get("volume")) for r in ohlc], dtype=float)
        dates = [str(r.get("date", "")) for r in ohlc]

        ema20 = self.ema(close, 20)
        ema50 = self.ema(close, 50)
        ma20 = self.sma(close, 20)
        rsi = self.wilder_rsi(close, self.RSI_PERIOD)
        macd_line, signal, hist = self.macd(close)

        window = min(self.SR_WINDOW, close.size)
        resistance = float(np.nanmax(high[-window:]))
        support = float(np.nanmin(low[-window:]))

        last_close = float(close[-1])
        last_ema20 = self._last(ema20)
        last_ema50 = self._last(ema50)
        last_rsi = self._last(rsi)
        last_macd = self._last(macd_line)
        last_signal = self._last(signal)

        trend = self._trend(last_close, last_ema20, last_ema50)
        momentum_signal = self._signal(last_rsi, last_macd, last_signal, trend)

        vol_avg20 = float(np.nanmean(volume[-20:])) if volume.size >= 20 else float(volume.mean())

        return {
            "last_close": rnd(last_close, 0),
            "ema20": rnd(last_ema20, 2),
            "ema50": rnd(last_ema50, 2),
            "ma20": rnd(self._last(ma20), 2),
            "rsi14": rnd(last_rsi, 2),
            "macd": rnd(last_macd, 3),
            "macd_signal": rnd(last_signal, 3),
            "macd_hist": rnd(self._last(hist), 3),
            "support": rnd(support, 0),
            "resistance": rnd(resistance, 0),
            "distance_to_support": rnd(safe_div(last_close - support, last_close), 4),
            "distance_to_resistance": rnd(safe_div(resistance - last_close, last_close), 4),
            "trend": trend,
            "signal": momentum_signal,
            "volume_avg20": rnd(vol_avg20, 0),
            "volume_last": rnd(float(volume[-1]), 0),
            "volume_ratio": rnd(safe_div(float(volume[-1]), vol_avg20), 2),
            "series": {
                "date": dates,
                "close": [rnd(x, 0) for x in close.tolist()],
                "open": [rnd(safe_float(r["open"]), 0) for r in ohlc],
                "high": [rnd(x, 0) for x in high.tolist()],
                "low": [rnd(x, 0) for x in low.tolist()],
                "volume": [rnd(x, 0) for x in volume.tolist()],
                "ema20": self._clean(ema20),
                "ema50": self._clean(ema50),
                "rsi14": self._clean(rsi),
                "macd": self._clean(macd_line),
                "macd_signal": self._clean(signal),
                "macd_hist": self._clean(hist),
            },
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _last(arr: np.ndarray) -> float:
        valid = arr[~np.isnan(arr)]
        return float(valid[-1]) if valid.size else 0.0

    @staticmethod
    def _clean(arr: np.ndarray) -> list[float | None]:
        return [None if np.isnan(x) else round(float(x), 3) for x in arr]

    @staticmethod
    def _trend(price: float, ema20: float, ema50: float) -> str:
        if ema20 == 0 or ema50 == 0:
            return "KHÔNG XÁC ĐỊNH"
        if price > ema20 > ema50:
            return "TĂNG"
        if price < ema20 < ema50:
            return "GIẢM"
        return "ĐI NGANG"

    @staticmethod
    def _signal(rsi: float, macd: float, signal: float, trend: str) -> str:
        score = 0
        if rsi < 30:
            score += 1
        elif rsi > 70:
            score -= 1
        if macd > signal:
            score += 1
        else:
            score -= 1
        if trend == "TĂNG":
            score += 1
        elif trend == "GIẢM":
            score -= 1

        if score >= 2:
            return "TÍCH CỰC"
        if score <= -2:
            return "TIÊU CỰC"
        return "TRUNG LẬP"

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {
            "last_close": 0.0, "ema20": 0.0, "ema50": 0.0, "ma20": 0.0,
            "rsi14": 50.0, "macd": 0.0, "macd_signal": 0.0, "macd_hist": 0.0,
            "support": 0.0, "resistance": 0.0, "distance_to_support": 0.0,
            "distance_to_resistance": 0.0, "trend": "KHÔNG XÁC ĐỊNH",
            "signal": "TRUNG LẬP", "volume_avg20": 0.0, "volume_last": 0.0,
            "volume_ratio": 0.0, "series": {},
            "error": "Chuỗi nến quá ngắn để tính chỉ báo kỹ thuật.",
        }
