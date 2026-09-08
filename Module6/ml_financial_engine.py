"""
Module6/ml_financial_engine.py
MACHINE LEARNING FINANCIAL ENGINE

Hai nhiệm vụ:

1. DỰ BÁO 3 KỊCH BẢN GIÁ (Random Forest Regressor)
   - Feature Engineering: Returns, Volatility (độ lệch chuẩn 10 phiên), MA20,
     khoảng cách giá so với MA20, momentum 5 phiên.
   - Mô hình: RandomForestRegressor(n_estimators=50) học quan hệ phi tuyến
     giữa đặc trưng ngày t và giá đóng cửa ngày t+H.
   - Base  = giá dự báo trung bình của mô hình
     Bull  = Base + 1.96 * sigma   (độ tin cậy 95%)
     Bear  = Base - 1.96 * sigma

2. CHẤM ĐIỂM PHÂN RÃ (Investment Score 0-100)
   Overall = 0.25*Fundamental + 0.25*Valuation + 0.20*Risk
           + 0.20*Quality + 0.10*Momentum
   Mỗi trụ cột dùng ánh xạ phi tuyến (hàm bão hoà) thay vì tuyến tính,
   để tránh việc một chỉ tiêu cực đoan kéo lệch toàn bộ điểm số.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from common.utils import clamp, rnd, safe_div, safe_float
from config import finance_config

try:
    from sklearn.ensemble import RandomForestRegressor

    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    RandomForestRegressor = None  # type: ignore[assignment, misc]
    SKLEARN_AVAILABLE = False


class MLFinancialEngine:
    """Bộ não học máy của nền tảng."""

    N_ESTIMATORS = 50
    HORIZON = 10          # dự báo giá đóng cửa sau 10 phiên (~2 tuần)
    MIN_SAMPLES = 60

    def __init__(self, config=finance_config) -> None:
        self.cfg = config

    # ------------------------------------------------------------------
    # 1. Feature Engineering
    # ------------------------------------------------------------------
    def build_features(self, close: np.ndarray, volume: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Trả về (X, y_index) — ma trận đặc trưng và chỉ số hàng tương ứng
        trên chuỗi giá gốc. Mỗi hàng là một phiên có đủ dữ liệu quá khứ.
        """
        n = close.size
        returns = np.zeros(n)
        returns[1:] = np.where(close[:-1] != 0, close[1:] / np.where(close[:-1] == 0, 1.0, close[:-1]) - 1.0, 0.0)

        vol10 = np.full(n, np.nan)
        ma20 = np.full(n, np.nan)
        mom5 = np.full(n, np.nan)
        vol_ratio = np.full(n, np.nan)

        for i in range(n):
            if i >= 10:
                vol10[i] = np.std(returns[i - 9: i + 1], ddof=1)
            if i >= 19:
                ma20[i] = close[i - 19: i + 1].mean()
            if i >= 5 and close[i - 5] != 0:
                mom5[i] = close[i] / close[i - 5] - 1.0
            if i >= 19:
                avg_v = volume[i - 19: i + 1].mean()
                vol_ratio[i] = volume[i] / avg_v if avg_v else 1.0

        dist_ma20 = np.where(ma20 > 0, close / ma20 - 1.0, np.nan)

        feats = np.column_stack([close, returns, vol10, ma20, dist_ma20, mom5, vol_ratio])
        valid = ~np.isnan(feats).any(axis=1)
        idx = np.where(valid)[0]
        return feats[valid], idx

    # ------------------------------------------------------------------
    # 2. Dự báo kịch bản giá
    # ------------------------------------------------------------------
    def predict_scenarios(self, ohlc: list[dict[str, Any]]) -> dict[str, Any]:
        close = np.asarray([safe_float(r.get("close")) for r in ohlc], dtype=float)
        volume = np.asarray([safe_float(r.get("volume")) for r in ohlc], dtype=float)
        last_price = safe_float(close[-1]) if close.size else 0.0

        if close.size < self.MIN_SAMPLES or not SKLEARN_AVAILABLE or RandomForestRegressor is None or last_price <= 0.0:
            return self._fallback_scenarios(close, last_price)

        X, idx = self.build_features(close, volume)
        if X.size == 0 or idx.size == 0:
            return self._fallback_scenarios(close, last_price)

        # Nhãn: giá đóng cửa sau HORIZON phiên
        target_idx = idx + self.HORIZON
        mask = target_idx < close.size
        if mask.sum() < 30:
            return self._fallback_scenarios(close, last_price)

        X_train = X[mask]
        y_train = close[target_idx[mask]]

        model = RandomForestRegressor(
            n_estimators=self.N_ESTIMATORS,
            max_depth=8,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=1,
        )
        model.fit(X_train, y_train)

        x_last = X[-1].reshape(1, -1)
        # Phân phối dự báo từ toàn bộ cây trong rừng -> đo bất định của mô hình
        tree_preds = np.asarray([t.predict(x_last)[0] for t in model.estimators_])
        base = safe_float(tree_preds.mean(), default=last_price)

        # Sigma tổng hợp: bất định mô hình + biến động lịch sử theo horizon
        model_sigma = safe_float(tree_preds.std(ddof=1)) if len(tree_preds) > 1 else 0.0
        rets = np.where(close[:-1] != 0, close[1:] / np.where(close[:-1] == 0, 1.0, close[:-1]) - 1.0, 0.0)
        hist_sigma = safe_float(np.std(rets, ddof=1)) * math.sqrt(self.HORIZON) * last_price if rets.size > 1 else 0.0
        sigma = math.sqrt(model_sigma ** 2 + hist_sigma ** 2)

        in_sample_r2 = safe_float(model.score(X_train, y_train))
        importances = dict(
            zip(
                ["close", "returns", "volatility_10d", "ma20", "dist_ma20", "momentum_5d", "volume_ratio"],
                [rnd(v, 4) for v in model.feature_importances_.tolist()],
            )
        )

        return self._pack_scenarios(base, sigma, last_price, {
            "model": f"RandomForestRegressor(n_estimators={self.N_ESTIMATORS})",
            "horizon_days": self.HORIZON,
            "train_samples": int(X_train.shape[0]),
            "r2_in_sample": rnd(in_sample_r2, 4),
            "model_sigma": rnd(model_sigma, 0),
            "historical_sigma": rnd(hist_sigma, 0),
            "feature_importances": importances,
        })

    def _fallback_scenarios(self, close: np.ndarray, last_price: float) -> dict[str, Any]:
        """Khi thiếu dữ liệu hoặc thiếu scikit-learn: dùng mô hình ngẫu nhiên bước."""
        if close.size < 3 or last_price <= 0.0:
            return self._pack_scenarios(last_price, 0.0, last_price,
                                        {"model": "Không đủ dữ liệu", "horizon_days": self.HORIZON})
        rets = np.where(close[:-1] != 0, close[1:] / np.where(close[:-1] == 0, 1.0, close[:-1]) - 1.0, 0.0)
        drift = safe_float(np.mean(rets)) * self.HORIZON
        sigma = safe_float(np.std(rets, ddof=1)) * math.sqrt(self.HORIZON) * last_price if rets.size > 1 else 0.0
        base = max(last_price * (1 + drift), 0.0)
        return self._pack_scenarios(base, sigma, last_price, {
            "model": "Random Walk (dự phòng)",
            "horizon_days": self.HORIZON,
            "note": "Thiếu dữ liệu hoặc scikit-learn để huấn luyện Random Forest.",
        })

    @staticmethod
    def _pack_scenarios(base: float, sigma: float, last_price: float,
                        meta: dict[str, Any]) -> dict[str, Any]:
        bull = base + 1.96 * sigma
        bear = max(base - 1.96 * sigma, 0.0)
        return {
            "base_case": rnd(base, 0),
            "bull_case": rnd(bull, 0),
            "bear_case": rnd(bear, 0),
            "sigma": rnd(sigma, 0),
            "confidence_level": 0.95,
            "current_price": rnd(last_price, 0),
            "base_return": rnd(safe_div(base - last_price, last_price), 4),
            "bull_return": rnd(safe_div(bull - last_price, last_price), 4),
            "bear_return": rnd(safe_div(bear - last_price, last_price), 4),
            "meta": meta,
        }

    # ------------------------------------------------------------------
    # 3. Chấm điểm 5 trụ cột
    # ------------------------------------------------------------------
    @staticmethod
    def _saturating(value: float, midpoint: float, steepness: float = 1.0) -> float:
        """
        Ánh xạ phi tuyến về [0, 100] bằng hàm logistic.
        value = midpoint -> 50 điểm; value >> midpoint -> tiệm cận 100.
        """
        try:
            x = steepness * (value - midpoint)
            return 100.0 / (1.0 + math.exp(-x))
        except OverflowError:
            return 0.0 if value < midpoint else 100.0

    def score_fundamental(self, f: dict[str, Any]) -> float:
        """Từ hàm hiệu suất ROE, có thưởng thêm theo ROIC và tăng trưởng."""
        roe = safe_float(f.get("roe"))
        roic = safe_float(f.get("roic"))
        growth = safe_float(f.get("revenue_cagr"))
        s_roe = self._saturating(roe, 0.15, 25)     # ROE 15% = 50 điểm
        s_roic = self._saturating(roic, 0.12, 25)
        s_growth = self._saturating(growth, 0.10, 20)
        return clamp(0.5 * s_roe + 0.3 * s_roic + 0.2 * s_growth, 0, 100)

    def score_valuation(self, v: dict[str, Any]) -> float:
        """So sánh giá trị nội tại DCF với thị giá + vị thế P/E so với ngành."""
        upside = safe_float(v.get("upside"))
        s_upside = self._saturating(upside, 0.10, 6)   # upside 10% = 50 điểm
        pe = safe_float(v.get("pe"))
        peer_pe = safe_float(v.get("peer_pe"))
        if pe > 0 and peer_pe > 0:
            discount = (peer_pe - pe) / peer_pe
            s_pe = self._saturating(discount, 0.0, 6)
        else:
            s_pe = 50.0
        return clamp(0.7 * s_upside + 0.3 * s_pe, 0, 100)

    def score_risk(self, r: dict[str, Any]) -> float:
        """Chuẩn hoá từ Altman Z-Score, trừ điểm theo biến động."""
        z = safe_float(r.get("altman", {}).get("z_score"))
        s_z = self._saturating(z, 2.40, 1.6)           # Z = 2.4 -> 50 điểm
        vol = safe_float(r.get("market", {}).get("annual_volatility"))
        s_vol = self._saturating(-vol, -0.35, 8)       # vol 35%/năm -> 50 điểm
        return clamp(0.7 * s_z + 0.3 * s_vol, 0, 100)

    def score_quality(self, f: dict[str, Any]) -> float:
        """Chất lượng lợi nhuận: khả năng chuyển hoá lợi nhuận thành tiền mặt."""
        conv = safe_float(f.get("cfo_to_net_income"))
        s_conv = self._saturating(conv, 1.0, 3.0)      # CFO/NI = 1.0 -> 50 điểm
        margin = safe_float(f.get("ebit_margin"))
        s_margin = self._saturating(margin, 0.12, 20)
        cr = safe_float(f.get("current_ratio"))
        s_cr = self._saturating(cr, 1.2, 2.0)
        return clamp(0.5 * s_conv + 0.3 * s_margin + 0.2 * s_cr, 0, 100)

    def score_momentum(self, f: dict[str, Any], t: dict[str, Any]) -> float:
        """Mức độ an toàn đòn bẩy kết hợp tín hiệu giá."""
        d_e = safe_float(f.get("debt_to_equity"))
        s_leverage = self._saturating(-d_e, -0.8, 2.5)  # D/E = 0.8 -> 50 điểm
        signal_map = {"TÍCH CỰC": 80.0, "TRUNG LẬP": 50.0, "TIÊU CỰC": 20.0}
        s_signal = signal_map.get(str(t.get("signal")), 50.0)
        rsi = safe_float(t.get("rsi14"), 50.0)
        s_rsi = 100.0 - abs(rsi - 55.0) * 2.0          # RSI quanh 55 là lý tưởng
        return clamp(0.4 * s_leverage + 0.4 * s_signal + 0.2 * clamp(s_rsi, 0, 100), 0, 100)

    def investment_score(self, fundamentals: dict[str, Any], valuation: dict[str, Any],
                         risk: dict[str, Any], technical: dict[str, Any]) -> dict[str, Any]:
        pillars = {
            "fundamental": rnd(self.score_fundamental(fundamentals), 1),
            "valuation": rnd(self.score_valuation(valuation), 1),
            "risk": rnd(self.score_risk(risk), 1),
            "quality": rnd(self.score_quality(fundamentals), 1),
            "momentum": rnd(self.score_momentum(fundamentals, technical), 1),
        }
        weights = {
            "fundamental": self.cfg.w_fundamental,
            "valuation": self.cfg.w_valuation,
            "risk": self.cfg.w_risk,
            "quality": self.cfg.w_quality,
            "momentum": self.cfg.w_momentum,
        }
        overall = sum(pillars[k] * weights[k] for k in pillars)

        return {
            "overall_score": rnd(overall, 1),
            "pillars": pillars,
            "weights": weights,
            "contributions": {k: rnd(pillars[k] * weights[k], 2) for k in pillars},
            "grade": self._grade(overall),
        }

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 80:
            return "A — Rất hấp dẫn"
        if score >= 65:
            return "B — Hấp dẫn"
        if score >= 50:
            return "C — Trung bình"
        if score >= 35:
            return "D — Kém hấp dẫn"
        return "E — Rủi ro cao"
