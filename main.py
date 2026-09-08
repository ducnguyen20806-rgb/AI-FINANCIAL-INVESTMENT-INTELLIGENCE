"""
main.py
API GATEWAY — FastAPI

Chạy:
    uvicorn main:app --reload --port 8000

Endpoint:
    GET  /                          -> thông tin dịch vụ
    GET  /health                    -> kiểm tra sống
    GET  /api/v1/analyze/{symbol}   -> phân tích toàn diện (Module 1-6)
    GET  /api/v1/quote/{symbol}     -> giá khớp lệnh
    GET  /api/v1/ohlc/{symbol}      -> chuỗi nến lịch sử
    GET  /api/v1/fundamental/{symbol}
    GET  /api/v1/technical/{symbol}
    GET  /api/v1/risk/{symbol}
"""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from Module1.data_source import get_data_source
from Module6.decision_engine import get_engine
from config import app_config

logging.basicConfig(
    level=getattr(logging, app_config.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("gateway")

app = FastAPI(
    title="AI Financial & Investment Intelligence Platform",
    description="Nền tảng phân tích tài chính và hỗ trợ quyết định đầu tư định lượng.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bộ nhớ đệm đơn giản trong tiến trình: {symbol: (timestamp, payload)}
_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def _cached(key: str) -> dict[str, Any] | None:
    hit = _cache.get(key)
    if not hit:
        return None
    ts, payload = hit
    if time.time() - ts > app_config.cache_ttl_seconds:
        _cache.pop(key, None)
        return None
    return payload


def _store(key: str, payload: dict[str, Any]) -> dict[str, Any]:
    _cache[key] = (time.time(), payload)
    return payload


def _clean_symbol(symbol: str) -> str:
    s = symbol.upper().strip()
    if not s.isalnum() or not (3 <= len(s) <= 10):
        raise HTTPException(status_code=400, detail=f"Mã chứng khoán không hợp lệ: {symbol}")
    return s


# ----------------------------------------------------------------------------
def _get_active_source() -> str:
    ds = get_data_source()
    return getattr(ds, "active_source", getattr(ds, "source_name", "UNKNOWN"))


def _get_analysis(symbol: str, refresh: bool = False) -> dict[str, Any]:
    sym = _clean_symbol(symbol)
    if not refresh:
        cached = _cached(f"analyze:{sym}")
        if cached:
            return cached
    try:
        result = get_engine().analyze(sym)
    except Exception as exc:  # noqa: BLE001 — biên giới dịch vụ
        logger.exception("Lỗi phân tích %s", sym)
        raise HTTPException(status_code=502, detail=f"Không phân tích được {sym}: {exc}") from exc
    return _store(f"analyze:{sym}", result)


# ----------------------------------------------------------------------------
@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "AI Financial & Investment Intelligence Platform",
        "version": "1.0.0",
        "data_source": _get_active_source(),
        "docs": "/docs",
        "endpoints": [
            "/api/v1/analyze/{symbol}",
            "/api/v1/quote/{symbol}",
            "/api/v1/ohlc/{symbol}",
            "/api/v1/fundamental/{symbol}",
            "/api/v1/technical/{symbol}",
            "/api/v1/risk/{symbol}",
        ],
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "data_source": _get_active_source()}


@app.get("/api/v1/analyze/{symbol}")
def analyze(symbol: str, refresh: bool = Query(False, description="Bỏ qua cache")) -> dict[str, Any]:
    """Phân tích toàn diện: 12 chỉ số, Investment Score, 3 kịch bản giá, nhật ký đầu tư."""
    return _get_analysis(symbol, refresh=bool(refresh))


@app.get("/api/v1/quote/{symbol}")
def quote(symbol: str) -> dict[str, Any]:
    sym = _clean_symbol(symbol)
    try:
        return get_data_source().get_quote(sym)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/v1/ohlc/{symbol}")
def ohlc(symbol: str, interval: str = "1D") -> dict[str, Any]:
    sym = _clean_symbol(symbol)
    try:
        rows = get_data_source().get_ohlc(sym, interval=interval)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"symbol": sym, "interval": interval, "count": len(rows), "data": rows}


@app.get("/api/v1/fundamental/{symbol}")
def fundamental(symbol: str) -> dict[str, Any]:
    res = _get_analysis(symbol)
    return {"symbol": res["symbol"], "fundamentals": res["fundamentals"]}


@app.get("/api/v1/technical/{symbol}")
def technical(symbol: str) -> dict[str, Any]:
    res = _get_analysis(symbol)
    return {"symbol": res["symbol"], "technical": res["technical"]}


@app.get("/api/v1/risk/{symbol}")
def risk(symbol: str) -> dict[str, Any]:
    res = _get_analysis(symbol)
    return {"symbol": res["symbol"], "risk": res["risk"]}


@app.get("/api/v1/sensitivity/{symbol}")
def sensitivity(symbol: str) -> dict[str, Any]:
    res = _get_analysis(symbol)
    return {"symbol": res["symbol"], "sensitivity": res.get("valuation", {}).get("sensitivity", {})}


@app.post("/api/v1/optimize_portfolio")
def optimize_portfolio(payload: dict[str, Any]) -> dict[str, Any]:
    symbols = payload.get("symbols", ["FPT", "HPG", "VNM", "MWG"])
    from common.utils import safe_float, to_returns
    from Module5.risk_engine import RiskEngine

    ds = get_data_source()
    returns_dict: dict[str, list[float]] = {}
    for s in symbols:
        try:
            ohlc_data = ds.get_ohlc(s)
            closes = [safe_float(r.get("close")) for r in ohlc_data]
            rets = to_returns(closes).tolist()
            if len(rets) >= 20:
                returns_dict[s] = rets
        except Exception:
            pass
    if len(returns_dict) < 2:
        raise HTTPException(status_code=400, detail="Cần tối thiểu 2 mã cổ phiếu có đủ dữ liệu để tối ưu danh mục.")
    return RiskEngine.optimize_portfolio(returns_dict)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=app_config.api_host, port=app_config.api_port, reload=True)
