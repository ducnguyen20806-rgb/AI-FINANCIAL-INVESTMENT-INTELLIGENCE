"""
Module1/data_source.py
REALTIME DATA PIPELINE & SSI ADAPTER

Chịu trách nhiệm kết nối, thu thập và chuẩn hoá toàn bộ dữ liệu thị trường
từ SSI FastConnect Data API v2. Áp dụng Adapter Pattern để cô lập hoàn toàn
tầng dữ liệu khỏi logic tính toán tài chính ở Module 2-6.

Cơ chế xác thực:
    POST {base_url}/Market/AccessToken  {consumerID, consumerSecret}
    -> JWT Bearer Token, tự động refresh sau 25 phút hoặc khi gặp 401.

Hàm public:
    get_quote(symbol)
    get_ohlc(symbol, start, end, interval)
    get_financial_ratios(symbol)
    get_index_ohlc(index_code)
    get_all_stock_data(symbol)   <- orchestrator
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any

import requests

from Module1.mock_source import MockDataSource
from common.utils import fmt_ssi_date, safe_float
from config import app_config, ssi_config

logger = logging.getLogger(__name__)


class SSIAuthError(RuntimeError):
    """Lỗi xác thực với SSI FastConnect."""


class SSIDataError(RuntimeError):
    """Lỗi truy vấn dữ liệu từ SSI FastConnect."""


class SSIDataSource:
    """Adapter dữ liệu thật — SSI FastConnect Data API v2."""

    source_name = "SSI"

    def __init__(self, config=ssi_config) -> None:
        self.cfg = config
        self._token: str | None = None
        self._token_ts: float = 0.0
        self._lock = threading.Lock()
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # 1. Xác thực
    # ------------------------------------------------------------------
    def _token_expired(self) -> bool:
        return (time.time() - self._token_ts) > self.cfg.token_ttl_seconds

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Lấy JWT Bearer Token, có cache và tự động refresh."""
        with self._lock:
            if self._token and not force_refresh and not self._token_expired():
                return self._token

            if not self.cfg.is_configured:
                raise SSIAuthError(
                    "Thiếu SSI_CONSUMER_ID / SSI_CONSUMER_SECRET trong file .env"
                )

            url = f"{self.cfg.base_url}/Market/AccessToken"
            payload = {
                "consumerID": self.cfg.consumer_id,
                "consumerSecret": self.cfg.consumer_secret,
            }
            try:
                resp = self._session.post(url, json=payload, timeout=self.cfg.timeout)
            except requests.RequestException as exc:
                raise SSIAuthError(f"Không kết nối được SSI: {exc}") from exc

            if resp.status_code != 200:
                raise SSIAuthError(
                    f"Xác thực SSI thất bại ({resp.status_code}): {resp.text[:200]}"
                )

            body = resp.json() or {}
            data = body.get("data") or {}
            token = data.get("accessToken") or body.get("accessToken")
            if not token:
                raise SSIAuthError(f"Phản hồi không chứa accessToken: {body}")

            # SSI trả token đã kèm tiền tố "Bearer " ở một số phiên bản
            self._token = token if token.startswith("Bearer") else f"Bearer {token}"
            self._token_ts = time.time()
            logger.info("Đã lấy AccessToken SSI thành công.")
            return self._token

    # ------------------------------------------------------------------
    # 2. Lớp gọi HTTP dùng chung
    # ------------------------------------------------------------------
    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """GET có tự động refresh token khi gặp 401 Unauthorized."""
        url = f"{self.cfg.base_url}{path}"
        last_error: str = ""

        for attempt in range(self.cfg.max_retry + 1):
            headers = {
                "Authorization": self.get_access_token(force_refresh=attempt > 0),
                "Content-Type": "application/json",
            }
            try:
                resp = self._session.get(
                    url, params=params, headers=headers, timeout=self.cfg.timeout
                )
            except requests.RequestException as exc:
                last_error = str(exc)
                time.sleep(0.6 * (attempt + 1))
                continue

            if resp.status_code == 401:
                logger.warning("Token hết hạn (401) — đang refresh...")
                last_error = "401 Unauthorized"
                continue
            if resp.status_code != 200:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                continue

            try:
                return resp.json() or {}
            except ValueError as exc:
                last_error = f"Phản hồi không phải JSON: {exc}"

        raise SSIDataError(f"Gọi {path} thất bại. {last_error}")

    @staticmethod
    def _rows(body: dict[str, Any]) -> list[dict[str, Any]]:
        """Chuẩn hoá phần data của phản hồi SSI về list[dict]."""
        data = body.get("data")
        if data is None:
            return []
        if isinstance(data, dict):
            return [data]
        return [r for r in data if isinstance(r, dict)]

    # ------------------------------------------------------------------
    # 3. Thu thập dữ liệu
    # ------------------------------------------------------------------
    def get_quote(self, symbol: str) -> dict[str, Any]:
        """
        Giá khớp lệnh gần nhất, biến động, khối lượng, giá trần/sàn/tham chiếu.
        Nguồn: /Market/DailyStockPrice (phiên gần nhất).
        """
        symbol = symbol.upper().strip()
        today = datetime.now()
        body = self._get(
            "/Market/DailyStockPrice",
            {
                "Symbol": symbol,
                "FromDate": fmt_ssi_date(today - timedelta(days=10)),
                "ToDate": fmt_ssi_date(today),
                "PageIndex": 1,
                "PageSize": 10,
                "market": "",
            },
        )
        rows = self._rows(body)
        if not rows:
            raise SSIDataError(f"Không có dữ liệu giá cho mã {symbol}")

        row = rows[0]  # SSI trả phiên mới nhất trước
        price = safe_float(row.get("ClosePrice") or row.get("MatchedPrice"))
        ref = safe_float(row.get("RefPrice"), default=price)
        change = price - ref
        return {
            "symbol": symbol,
            "price": price,
            "ref_price": ref,
            "ceiling": safe_float(row.get("CeilingPrice"), default=round(ref * 1.07)),
            "floor": safe_float(row.get("FloorPrice"), default=round(ref * 0.93)),
            "open": safe_float(row.get("OpenPrice"), default=price),
            "high": safe_float(row.get("HighestPrice"), default=price),
            "low": safe_float(row.get("LowestPrice"), default=price),
            "change": round(change, 2),
            "change_pct": round(change / ref * 100, 2) if ref else 0.0,
            "volume": safe_float(row.get("TotalMatchVol")),
            "value": safe_float(row.get("TotalMatchVal")),
            "trading_date": str(row.get("TradingDate") or today.strftime("%d/%m/%Y")),
            "exchange": str(row.get("Market") or ""),
        }

    def get_ohlc(self, symbol: str, start: str | None = None,
                 end: str | None = None, interval: str = "1D") -> list[dict[str, Any]]:
        """
        Chuỗi nến lịch sử OHLCV. Mặc định lấy 1 năm gần nhất.
        Nguồn: /Market/DailyOhlc (interval='1D') hoặc /Market/IntradayOhlc.
        """
        symbol = symbol.upper().strip()
        today = datetime.now()
        from_date = start or fmt_ssi_date(today - timedelta(days=400))
        to_date = end or fmt_ssi_date(today)
        path = "/Market/DailyOhlc" if interval.upper() == "1D" else "/Market/IntradayOhlc"

        rows: list[dict[str, Any]] = []
        page = 1
        while page <= 10:  # chặn trên để tránh vòng lặp vô hạn
            body = self._get(
                path,
                {
                    "Symbol": symbol,
                    "FromDate": from_date,
                    "ToDate": to_date,
                    "PageIndex": page,
                    "PageSize": 100,
                    "ascending": True,
                },
            )
            chunk = self._rows(body)
            if not chunk:
                break
            rows.extend(chunk)
            if len(chunk) < 100:
                break
            page += 1

        out: list[dict[str, Any]] = []
        for r in rows:
            raw_date = str(r.get("TradingDate") or r.get("Date") or "")
            out.append(
                {
                    "date": self._norm_date(raw_date),
                    "open": safe_float(r.get("Open")),
                    "high": safe_float(r.get("High")),
                    "low": safe_float(r.get("Low")),
                    "close": safe_float(r.get("Close")),
                    "volume": safe_float(r.get("Volume")),
                    "value": safe_float(r.get("Value")),
                }
            )
        out = [r for r in out if r["close"] > 0]
        out.sort(key=lambda r: r["date"])
        if not out:
            raise SSIDataError(f"Không có dữ liệu OHLC cho mã {symbol}")
        return out

    @staticmethod
    def _norm_date(raw: str) -> str:
        """Chuẩn hoá dd/MM/yyyy -> yyyy-MM-dd."""
        raw = raw.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return raw

    def get_index_ohlc(self, index_code: str = "VNINDEX") -> list[dict[str, Any]]:
        """Chuỗi giá đóng cửa chỉ số thị trường phục vụ tính Beta."""
        today = datetime.now()
        body = self._get(
            "/Market/DailyIndex",
            {
                "Indexcode": index_code,
                "FromDate": fmt_ssi_date(today - timedelta(days=400)),
                "ToDate": fmt_ssi_date(today),
                "PageIndex": 1,
                "PageSize": 300,
                "OrderBy": "Tradingdate",
                "Order": "asc",
            },
        )
        out = [
            {
                "date": self._norm_date(str(r.get("TradingDate") or "")),
                "close": safe_float(r.get("IndexValue")),
            }
            for r in self._rows(body)
        ]
        out = [r for r in out if r["close"] > 0]
        out.sort(key=lambda r: r["date"])
        return out

    def get_financial_ratios(self, symbol: str) -> dict[str, Any]:
        """
        Báo cáo tài chính & chỉ số tài chính (ROE, ROIC, P/E, P/B, Nợ/CSH,
        CFO, biên lợi nhuận).

        Lưu ý vận hành: endpoint báo cáo tài chính phụ thuộc gói dịch vụ
        FastConnect đã đăng ký. Nếu endpoint không khả dụng, hàm ném
        SSIDataError để tầng orchestrator quyết định fallback.
        """
        symbol = symbol.upper().strip()
        body = self._get(
            self.cfg.financial_endpoint,
            {"Symbol": symbol, "PageIndex": 1, "PageSize": 12, "Period": "Q"},
        )
        rows = self._rows(body)
        if not rows:
            raise SSIDataError(f"Không có dữ liệu BCTC cho mã {symbol}")

        periods: list[dict[str, Any]] = []
        for r in rows:
            periods.append(
                {
                    "period": str(r.get("Period") or f"{r.get('YearReport','')}Q{r.get('LengthReport','')}"),
                    "revenue": safe_float(r.get("Revenue") or r.get("NetRevenue")),
                    "gross_profit": safe_float(r.get("GrossProfit")),
                    "ebit": safe_float(r.get("EBIT") or r.get("OperatingProfit")),
                    "net_income": safe_float(r.get("NetIncome") or r.get("ProfitAfterTax")),
                    "cfo": safe_float(r.get("CFO") or r.get("NetCashFlowFromOperating")),
                    "capex": safe_float(r.get("Capex") or r.get("PurchaseOfFixedAssets")),
                    "total_assets": safe_float(r.get("TotalAssets")),
                    "current_assets": safe_float(r.get("CurrentAssets")),
                    "current_liabilities": safe_float(r.get("CurrentLiabilities")),
                    "total_liabilities": safe_float(r.get("TotalLiabilities") or r.get("Liability")),
                    "equity": safe_float(r.get("OwnersEquity") or r.get("Equity")),
                    "retained_earnings": safe_float(r.get("RetainedEarnings")),
                    "short_debt": safe_float(r.get("ShortTermDebt")),
                    "long_debt": safe_float(r.get("LongTermDebt")),
                    "interest_expense": safe_float(r.get("InterestExpense")),
                    "cash": safe_float(r.get("CashAndEquivalents")),
                }
            )
        periods.sort(key=lambda p: p["period"])

        return {
            "periods": periods,
            "shares_outstanding": safe_float(rows[0].get("SharesOutstanding")),
            "sector": str(rows[0].get("Sector") or ""),
            "peers": {
                "pe": safe_float(rows[0].get("IndustryPE"), default=0.0),
                "pb": safe_float(rows[0].get("IndustryPB"), default=0.0),
                "roe": safe_float(rows[0].get("IndustryROE"), default=0.0),
            },
        }

    # ------------------------------------------------------------------
    # 4. Orchestrator
    # ------------------------------------------------------------------
    def get_all_stock_data(self, symbol: str) -> dict[str, Any]:
        """Gom Realtime + OHLC 1 năm + BCTC chỉ qua một câu gọi duy nhất."""
        symbol = symbol.upper().strip()
        warnings: list[str] = []

        quote = self.get_quote(symbol)
        ohlc = self.get_ohlc(symbol)

        try:
            index_ohlc = self.get_index_ohlc()
        except SSIDataError as exc:
            logger.warning("Không lấy được chỉ số thị trường: %s", exc)
            index_ohlc = []
            warnings.append("Không lấy được VNINDEX — Beta dùng giá trị mặc định.")

        try:
            financials = self.get_financial_ratios(symbol)
        except SSIDataError as exc:
            logger.warning("Không lấy được BCTC từ SSI: %s", exc)
            financials = MockDataSource().get_financial_ratios(symbol)
            warnings.append(
                "Endpoint BCTC không khả dụng — dùng dữ liệu tài chính mô phỏng "
                "cho Module 2/3/5."
            )

        return {
            "symbol": symbol,
            "source": self.source_name,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "quote": quote,
            "ohlc": ohlc,
            "index_ohlc": index_ohlc,
            "financials": financials,
            "warnings": warnings,
        }


# ----------------------------------------------------------------------------
# Factory + lớp bọc fallback
# ----------------------------------------------------------------------------
class UserAPIDataSource:
    """
    Lớp mặt tiền (Facade) mà Module 6 và API Gateway sử dụng.

    Tự chọn adapter: SSI nếu đã cấu hình khoá, ngược lại dùng Mock.
    Nếu SSI lỗi và FALLBACK_TO_MOCK=true thì tự động rơi về Mock để
    hệ thống không gãy giữa phiên phân tích.
    """

    def __init__(self) -> None:
        self.mock = MockDataSource()
        self.ssi: SSIDataSource | None = None
        if ssi_config.is_configured and not app_config.use_mock:
            self.ssi = SSIDataSource()

    @property
    def active_source(self) -> str:
        return "SSI" if self.ssi else "MOCK"

    def _delegate(self, method: str, *args, **kwargs):
        if self.ssi is not None:
            try:
                return getattr(self.ssi, method)(*args, **kwargs)
            except (SSIAuthError, SSIDataError, requests.RequestException) as exc:
                logger.error("SSI lỗi ở %s: %s", method, exc)
                if not app_config.fallback_to_mock:
                    raise
        return getattr(self.mock, method)(*args, **kwargs)

    def get_quote(self, symbol: str):
        return self._delegate("get_quote", symbol)

    def get_ohlc(self, symbol: str, start=None, end=None, interval: str = "1D"):
        return self._delegate("get_ohlc", symbol, start, end, interval)

    def get_financial_ratios(self, symbol: str):
        return self._delegate("get_financial_ratios", symbol)

    def get_index_ohlc(self, index_code: str = "VNINDEX"):
        return self._delegate("get_index_ohlc", index_code)

    def get_all_stock_data(self, symbol: str):
        return self._delegate("get_all_stock_data", symbol)


_default_source: UserAPIDataSource | None = None


def get_data_source() -> UserAPIDataSource:
    """Singleton nguồn dữ liệu dùng chung cho toàn hệ thống."""
    global _default_source
    if _default_source is None:
        _default_source = UserAPIDataSource()
    return _default_source
