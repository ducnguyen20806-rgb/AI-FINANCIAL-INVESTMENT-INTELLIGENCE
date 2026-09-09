"""
Module1/cache_manager.py
BỘ NHỚ ĐỆM TỐC ĐỘ CAO (HIGH-SPEED STALE-WHILE-REVALIDATE CACHE ENGINE)

Cơ chế:
1. Đọc dữ liệu từ RAM/Disk chỉ mất 1-2 ms.
2. Áp dụng Stale-While-Revalidate: Trả về dữ liệu đệm ngay lập tức, cập nhật ngầm nếu quá thời hạn.
3. Đảm bảo tốc độ mở Dashboard luôn đạt mức tức thì (< 0.1s).
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Bộ nhớ đệm cấp 1: RAM Cache
_MEM_CACHE: dict[str, tuple[dict[str, Any], float]] = {}
_MEM_LOCK = threading.Lock()

# Tránh tạo nhiều luồng cập nhật ngầm cho cùng một mã
_UPDATING_SYMBOLS: set[str] = set()
_UPDATING_LOCK = threading.Lock()


def _get_cache_path(symbol: str) -> Path:
    return CACHE_DIR / f"{symbol.upper().strip()}.json"


def save_to_cache(symbol: str, data: dict[str, Any]) -> None:
    """Lưu gói dữ liệu vào cả RAM và file đĩa JSON."""
    symbol = symbol.upper().strip()
    now = time.time()
    with _MEM_LOCK:
        _MEM_CACHE[symbol] = (data, now)

    try:
        path = _get_cache_path(symbol)
        temp_path = path.with_suffix(".tmp")
        payload = {
            "cached_at": now,
            "data": data,
        }
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        temp_path.replace(path)
    except Exception as exc:
        logger.warning("Không thể ghi cache đĩa cho %s: %s", symbol, exc)


def load_from_cache(symbol: str, max_age: float | None = None) -> dict[str, Any] | None:
    """Đọc dữ liệu từ RAM trước, nếu không có đọc từ đĩa."""
    symbol = symbol.upper().strip()
    now = time.time()

    # 1. Thử đọc từ RAM
    with _MEM_LOCK:
        cached = _MEM_CACHE.get(symbol)
        if cached is not None:
            data, ts = cached
            if max_age is None or (now - ts) <= max_age:
                return data

    # 2. Thử đọc từ Đĩa
    path = _get_cache_path(symbol)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        ts = float(payload.get("cached_at", 0))
        data = payload.get("data")
        if isinstance(data, dict):
            if max_age is None or (now - ts) <= max_age:
                with _MEM_LOCK:
                    _MEM_CACHE[symbol] = (data, ts)
                return data
    except Exception as exc:
        logger.warning("Không thể đọc cache đĩa cho %s: %s", symbol, exc)

    return None


def get_cached_or_fetch(
    symbol: str,
    fetch_func: Callable[[str], dict[str, Any]],
    max_age_seconds: float = 86400.0,
    background_refresh: bool = False,
) -> dict[str, Any]:
    """
    Mô hình Stale-While-Revalidate:
    - Nếu có cache (kể cả cũ): Trả về NGAY LẬP TỨC (<2ms).
    - Nếu cache đã quá hạn: Khởi chạy luồng chạy ngầm cập nhật dữ liệu mà không chặn người dùng.
    - Nếu chưa từng có cache: Buộc phải gọi hàm tải trực tiếp lần đầu rồi lưu lại.
    """
    symbol = symbol.upper().strip()
    now = time.time()

    # Thử lấy dữ liệu từ cache (bất kể mới hay cũ)
    cached_data = load_from_cache(symbol, max_age=None)

    if cached_data is not None:
        # Kiểm tra xem cache có bị cũ không
        path = _get_cache_path(symbol)
        mtime = path.stat().st_mtime if path.exists() else 0
        is_stale = (now - mtime) > max_age_seconds

        if is_stale and background_refresh:
            # Khởi chạy luồng cập nhật ngầm nếu chưa có luồng nào đang chạy cho mã này
            with _UPDATING_LOCK:
                if symbol not in _UPDATING_SYMBOLS:
                    _UPDATING_SYMBOLS.add(symbol)

                    def _bg_worker():
                        try:
                            fresh = fetch_func(symbol)
                            if fresh and isinstance(fresh, dict):
                                save_to_cache(symbol, fresh)
                                logger.info("Đã cập nhật dữ liệu ngầm cho %s thành công", symbol)
                        except Exception as err:
                            logger.warning("Lỗi cập nhật dữ liệu ngầm cho %s: %s", symbol, err)
                        finally:
                            with _UPDATING_LOCK:
                                _UPDATING_SYMBOLS.discard(symbol)

                    t = threading.Thread(target=_bg_worker, daemon=True)
                    t.start()

        return cached_data

    # Chưa có cache: Tải trực tiếp và lưu vào cache
    fresh = fetch_func(symbol)
    if fresh and isinstance(fresh, dict):
        save_to_cache(symbol, fresh)
    return fresh

