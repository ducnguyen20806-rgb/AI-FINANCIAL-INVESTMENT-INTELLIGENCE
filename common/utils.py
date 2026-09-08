"""
common/utils.py
Các hàm tiện ích dùng chung: chia an toàn, ép kiểu số, chuẩn hoá chuỗi giá,
tính lợi suất, định dạng số theo chuẩn Việt Nam.

Nguyên tắc: KHÔNG BAO GIỜ ném ZeroDivisionError / NaN ra tầng trên.
Mọi phép chia tài chính đều đi qua safe_div().
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any, Iterable, Sequence

import numpy as np

# ----------------------------------------------------------------------------
# Số học an toàn
# ----------------------------------------------------------------------------


def safe_float(value: Any, default: float = 0.0) -> float:
    """Ép kiểu về float, trả về default nếu None/rỗng/không hợp lệ/NaN."""
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    try:
        if isinstance(value, str):
            value = value.replace(",", "").replace(" ", "").strip()
            if value in ("", "-", "N/A", "null", "None"):
                return default
        out = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(out) or math.isinf(out):
        return default
    return out


def safe_div(numerator: Any, denominator: Any, default: float = 0.0) -> float:
    """Phép chia an toàn: mẫu số 0 hoặc không hợp lệ -> trả về default."""
    num = safe_float(numerator, default=float("nan"))
    den = safe_float(denominator, default=float("nan"))
    if math.isnan(num) or math.isnan(den) or den == 0:
        return default
    result = num / den
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def clamp(value: Any, low: float, high: float) -> float:
    """Giới hạn giá trị trong đoạn [low, high]."""
    return max(low, min(high, safe_float(value)))


def pct(value: Any, digits: int = 2) -> float:
    """Đổi tỷ lệ thập phân sang phần trăm, làm tròn."""
    return round(safe_float(value) * 100.0, digits)


def rnd(value: Any, digits: int = 2) -> float:
    """Làm tròn an toàn."""
    return round(safe_float(value), digits)


# ----------------------------------------------------------------------------
# Chuỗi thời gian
# ----------------------------------------------------------------------------


def to_returns(prices: Sequence[float]) -> np.ndarray:
    """
    Tính chuỗi tỷ suất sinh lời đơn giản r_t = P_t / P_{t-1} - 1.

    Không dùng pandas.pct_change() để tương thích mọi phiên bản pandas
    (fill_method bị loại bỏ từ pandas 3.0).
    """
    arr = np.asarray([safe_float(p) for p in prices], dtype=float)
    if arr.size < 2:
        return np.asarray([], dtype=float)
    prev = arr[:-1]
    curr = arr[1:]
    with np.errstate(divide="ignore", invalid="ignore"):
        rets = np.where(prev != 0, curr / np.where(prev == 0, np.nan, prev) - 1.0, 0.0)
    rets = np.nan_to_num(rets, nan=0.0, posinf=0.0, neginf=0.0)
    return rets


def cagr(begin_value: float, end_value: float, years: float) -> float:
    """Tốc độ tăng trưởng kép CAGR. Trả về 0 nếu dữ liệu không hợp lệ."""
    b = safe_float(begin_value)
    e = safe_float(end_value)
    y = safe_float(years)
    if b <= 0 or e <= 0 or y <= 0:
        return 0.0
    try:
        return (e / b) ** (1.0 / y) - 1.0
    except (ValueError, OverflowError):
        return 0.0


def trading_days_ago(days: int) -> datetime:
    """Mốc thời gian lùi về quá khứ theo số ngày lịch."""
    return datetime.now() - timedelta(days=days)


def fmt_ssi_date(dt: datetime) -> str:
    """SSI FastConnect yêu cầu định dạng dd/MM/yyyy."""
    return dt.strftime("%d/%m/%Y")


# ----------------------------------------------------------------------------
# Định dạng hiển thị (dùng cho tầng UI)
# ----------------------------------------------------------------------------


def fmt_vnd(value: Any, unit: str = "auto") -> str:
    """
    Định dạng tiền VNĐ theo quy ước Việt Nam.
    unit='auto' tự chọn tỷ / triệu / đồng.
    """
    v = safe_float(value)
    sign = "-" if v < 0 else ""
    v = abs(v)
    if unit == "auto":
        if v >= 1_000_000_000_000:
            return f"{sign}{v / 1_000_000_000_000:,.2f} nghìn tỷ"
        if v >= 1_000_000_000:
            return f"{sign}{v / 1_000_000_000:,.2f} tỷ"
        if v >= 1_000_000:
            return f"{sign}{v / 1_000_000:,.2f} triệu"
    return f"{sign}{v:,.0f} đ"


def fmt_num(value: Any, digits: int = 2) -> str:
    """Định dạng số thường có phân tách hàng nghìn."""
    return f"{safe_float(value):,.{digits}f}"


def first_valid(values: Iterable[Any], default: float = 0.0) -> float:
    """Lấy giá trị số hợp lệ đầu tiên khác 0 trong danh sách."""
    for v in values:
        f = safe_float(v, default=0.0)
        if f != 0.0:
            return f
    return default
