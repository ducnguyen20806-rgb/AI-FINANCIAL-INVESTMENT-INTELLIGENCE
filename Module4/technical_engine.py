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
            "triggers": self.scan_triggers(close, ema20, ema50, rsi, macd_line, signal, volume),
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
    def scan_triggers(close: np.ndarray, ema20: np.ndarray, ema50: np.ndarray,
                      rsi: np.ndarray, macd_line: np.ndarray, signal_line: np.ndarray,
                      volume: np.ndarray) -> dict[str, Any]:
        """
        Quét các điểm kích hoạt tín hiệu định lượng (Quant Algorithmic Triggers):
        1. Golden Cross / Death Cross
        2. RSI Divergence (Phân kỳ tăng / giảm)
        3. Bollinger Band Squeeze & Breakout
        4. Volume Spike (Đột biến khối lượng dòng tiền tổ chức)
        5. MACD Momentum Crossover
        """
        n = close.size
        if n < 20:
            return {
                "overall_action": "THEO DÕI",
                "net_score": 0,
                "bullish_triggers": 0,
                "bearish_triggers": 0,
                "triggers_list": [],
            }

        triggers: list[dict[str, Any]] = []
        bull_count = 0
        bear_count = 0

        # 1. EMA Trend & Crossover
        if not np.isnan(ema20[-1]) and not np.isnan(ema50[-1]):
            e20_now, e50_now = ema20[-1], ema50[-1]
            e20_prev = ema20[-5] if n >= 5 and not np.isnan(ema20[-5]) else e20_now
            e50_prev = ema50[-5] if n >= 5 and not np.isnan(ema50[-5]) else e50_now

            if e20_prev <= e50_prev and e20_now > e50_now:
                triggers.append({
                    "name": "Golden Cross (Giao cắt vàng)",
                    "type": "BULLISH",
                    "badge": "⚡ ĐỘT PHÁ",
                    "desc": "EMA 20 vừa cắt lên trên EMA 50 — Tín hiệu xác lập sóng tăng trung hạn.",
                    "priority": "HIGH",
                })
                bull_count += 2
            elif e20_now > e50_now and close[-1] > e20_now:
                triggers.append({
                    "name": "EMA 20/50 Bullish Alignment",
                    "type": "BULLISH",
                    "badge": "🟢 TÍCH CỰC",
                    "desc": "Thị giá nằm trên dải EMA 20 và EMA 50 hướng lên vững chắc.",
                    "priority": "MEDIUM",
                })
                bull_count += 1
            elif e20_now < e50_now and close[-1] < e20_now:
                triggers.append({
                    "name": "EMA 20/50 Bearish Alignment",
                    "type": "BEARISH",
                    "badge": "🔴 TIÊU CỰC",
                    "desc": "Thị giá nằm dưới EMA 20 và EMA 50 hướng xuống — Xu hướng giảm chi phối.",
                    "priority": "MEDIUM",
                })
                bear_count += 1

        # 2. RSI Divergence / Overbought / Oversold
        valid_rsi = rsi[~np.isnan(rsi)]
        if valid_rsi.size >= 10:
            rsi_now = float(valid_rsi[-1])
            if rsi_now <= 30:
                triggers.append({
                    "name": "RSI Oversold (Quá bán sâu)",
                    "type": "BULLISH",
                    "badge": "💎 VÙNG MUA",
                    "desc": f"RSI({rsi_now:.1f}) chạm vùng quá bán — Kỳ vọng nhịp phục hồi kỹ thuật ngắn hạn.",
                    "priority": "HIGH",
                })
                bull_count += 1
            elif rsi_now >= 70:
                triggers.append({
                    "name": "RSI Overbought (Quá mua cao)",
                    "type": "BEARISH",
                    "badge": "⚠️ CẢNH BÁO",
                    "desc": f"RSI({rsi_now:.1f}) đi vào vùng quá mua — Áp lực chốt lời ngắn hạn gia tăng.",
                    "priority": "HIGH",
                })
                bear_count += 1

            # Phân kỳ RSI đơn giản 20 phiên
            if n >= 20 and valid_rsi.size >= 15:
                if close[-1] < close[-15] and valid_rsi[-1] > valid_rsi[-15] and valid_rsi[-1] < 45:
                    triggers.append({
                        "name": "Phân kỳ Dương RSI (Bullish Divergence)",
                        "type": "BULLISH",
                        "badge": "🚀 TÍN HIỆU ĐẢO CHIỀU",
                        "desc": "Giá tạo đáy thấp hơn nhưng RSI tạo đáy cao hơn — Dấu hiệu phân kỳ đảo chiều tăng.",
                        "priority": "VERY_HIGH",
                    })
                    bull_count += 2

        # 3. Bollinger Band Squeeze & Breakout
        if n >= 20:
            sma20 = float(np.mean(close[-20:]))
            std20 = float(np.std(close[-20:]))
            upper = sma20 + 2.0 * std20
            lower = sma20 - 2.0 * std20
            bw = (upper - lower) / sma20 if sma20 > 0 else 0.0

            if close[-1] > upper:
                triggers.append({
                    "name": "Bollinger Upper Breakout",
                    "type": "BULLISH",
                    "badge": "⚡ BỨT PHÁ DẢI TRÊN",
                    "desc": "Thị giá đóng cửa vượt ra ngoài dải Bollinger Band trên cùng động lượng mạnh.",
                    "priority": "MEDIUM",
                })
                bull_count += 1
            elif close[-1] < lower:
                triggers.append({
                    "name": "Bollinger Lower Penetration",
                    "type": "BEARISH",
                    "badge": "⚠️ THỦNG DẢI DƯỚI",
                    "desc": "Thị giá rơi qua dải Bollinger dưới — Cần quản trị rủi ro mở rộng biên độ giảm.",
                    "priority": "MEDIUM",
                })
                bear_count += 1
            elif bw < 0.05:
                triggers.append({
                    "name": "Bollinger Band Squeeze (Nén biến động)",
                    "type": "NEUTRAL",
                    "badge": "⏳ NÉN BIẾN ĐỘNG",
                    "desc": f"Độ mở dải Bollinger co hẹp ({bw*100:.1f}%) — Báo hiệu sắp có pha bứt phá mạnh.",
                    "priority": "MEDIUM",
                })

        # 4. Volume Spike
        if n >= 20 and volume.size >= 20:
            v_avg20 = float(np.mean(volume[-20:]))
            v_now = float(volume[-1])
            v_ratio = v_now / v_avg20 if v_avg20 > 0 else 1.0

            if v_ratio >= 1.8 and close[-1] > close[-2]:
                triggers.append({
                    "name": "Institutional Volume Accumulation",
                    "type": "BULLISH",
                    "badge": "🔥 DÒNG TIỀN VÀO",
                    "desc": f"Khối lượng khớp lệnh phiên đạt {v_ratio:.1f}x trung bình 20 phiên kèm giá tăng mạnh.",
                    "priority": "HIGH",
                })
                bull_count += 2
            elif v_ratio >= 1.8 and close[-1] < close[-2]:
                triggers.append({
                    "name": "Heavy Distribution Volume",
                    "type": "BEARISH",
                    "badge": "🩸 DÒNG TIỀN THOÁT",
                    "desc": f"Khối lượng phiên bán tháo đạt {v_ratio:.1f}x trung bình 20 phiên.",
                    "priority": "HIGH",
                })
                bear_count += 2

        # 5. MACD Crossover
        valid_macd = macd_line[~np.isnan(macd_line)]
        valid_sig = signal_line[~np.isnan(signal_line)]
        if valid_macd.size >= 2 and valid_sig.size >= 2:
            m_now, s_now = valid_macd[-1], valid_sig[-1]
            m_prev, s_prev = valid_macd[-2], valid_sig[-2]
            if m_prev <= s_prev and m_now > s_now:
                triggers.append({
                    "name": "MACD Bullish Crossover",
                    "type": "BULLISH",
                    "badge": "📈 GIAO CẮT MUA",
                    "desc": "Đường MACD vừa cắt lên trên đường Signal — Xác nhận xung lượng tăng giá mở rộng.",
                    "priority": "HIGH",
                })
                bull_count += 2
            elif m_prev >= s_prev and m_now < s_now:
                triggers.append({
                    "name": "MACD Bearish Crossover",
                    "type": "BEARISH",
                    "badge": "📉 GIAO CẮT BÁN",
                    "desc": "Đường MACD vừa cắt xuống dưới đường Signal — Xung lượng giảm hình thành.",
                    "priority": "HIGH",
                })
                bear_count += 2

        # Đánh giá tổng hợp
        net_score = bull_count - bear_count
        if net_score >= 3:
            overall = "MUA MẠNH (STRONG BUY)"
        elif net_score >= 1:
            overall = "MUA TÍCH LŨY (ACCUMULATE)"
        elif net_score <= -3:
            overall = "HẠ TỶ TRỌNG / BÁN (SELL)"
        elif net_score <= -1:
            overall = "THẬN TRỌNG (CAUTION)"
        else:
            overall = "THEO DÕI (NEUTRAL)"

        return {
            "overall_action": overall,
            "net_score": net_score,
            "bullish_triggers": bull_count,
            "bearish_triggers": bear_count,
            "triggers_list": triggers,
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
            "volume_ratio": 0.0,
            "triggers": {
                "overall_action": "THEO DÕI",
                "net_score": 0,
                "bullish_triggers": 0,
                "bearish_triggers": 0,
                "triggers_list": [],
            },
            "series": {},
            "error": "Chuỗi nến quá ngắn để tính chỉ báo kỹ thuật.",
        }
