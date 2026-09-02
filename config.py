"""
config.py
Cấu hình tập trung toàn hệ thống. Đọc biến môi trường từ file .env.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

try:  # python-dotenv là tuỳ chọn, hệ thống vẫn chạy nếu thiếu
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key, str(default)).strip().lower()
    return raw in ("1", "true", "yes", "y", "on")


@dataclass
class SSIConfig:
    """Thông số kết nối SSI FastConnect Data API v2."""

    consumer_id: str = field(default_factory=lambda: _env("SSI_CONSUMER_ID"))
    consumer_secret: str = field(default_factory=lambda: _env("SSI_CONSUMER_SECRET"))
    base_url: str = field(
        default_factory=lambda: _env("SSI_BASE_URL", "https://fc-data.ssi.com.vn/api/v2")
    )
    # Endpoint báo cáo tài chính có thể khác nhau theo gói dịch vụ đăng ký.
    financial_endpoint: str = field(
        default_factory=lambda: _env("SSI_FINANCIAL_ENDPOINT", "/Market/CompanyFinancialRatio")
    )
    token_ttl_seconds: int = 25 * 60  # tự động refresh sau 25 phút
    timeout: int = 15
    max_retry: int = 2

    @property
    def is_configured(self) -> bool:
        return bool(self.consumer_id and self.consumer_secret)


@dataclass
class FinanceConfig:
    """Tham số mô hình định giá & rủi ro (thị trường Việt Nam)."""

    risk_free_rate: float = field(default_factory=lambda: _env_float("RISK_FREE_RATE", 0.030))
    equity_risk_premium: float = field(default_factory=lambda: _env_float("EQUITY_RISK_PREMIUM", 0.080))
    corporate_tax_rate: float = field(default_factory=lambda: _env_float("CORPORATE_TAX_RATE", 0.20))
    terminal_growth: float = field(default_factory=lambda: _env_float("TERMINAL_GROWTH", 0.030))
    forecast_years: int = 5
    trading_days_per_year: int = 250
    default_beta: float = 1.0
    market_index: str = field(default_factory=lambda: _env("MARKET_INDEX", "VNINDEX"))

    # Trọng số Investment Score (tổng = 1.0)
    w_fundamental: float = 0.25
    w_valuation: float = 0.25
    w_risk: float = 0.20
    w_quality: float = 0.20
    w_momentum: float = 0.10

    # Ngưỡng quản trị vị thế
    stop_loss_ratio: float = 0.90  # Stop price = Price * 0.90
    max_position_size: float = 0.15  # tối đa 15% NAV cho 1 mã


@dataclass
class AppConfig:
    """Cấu hình ứng dụng."""

    api_host: str = field(default_factory=lambda: _env("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(_env_float("API_PORT", 8000)))
    api_base_url: str = field(
        default_factory=lambda: _env("API_BASE_URL", "http://localhost:8000")
    )
    # Tắt hoàn toàn chế độ dữ liệu mô phỏng
    use_mock: bool = field(default_factory=lambda: _env_bool("USE_MOCK", False))
    # TẮT tự động rơi về mô phỏng (Đổi default sang False để không dùng Mock nữa)
    fallback_to_mock: bool = field(default_factory=lambda: _env_bool("FALLBACK_TO_MOCK", False))
    cache_ttl_seconds: int = field(default_factory=lambda: int(_env_float("CACHE_TTL", 120)))
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))


ssi_config = SSIConfig()
finance_config = FinanceConfig()
app_config = AppConfig()

__all__ = ["ssi_config", "finance_config", "app_config", "SSIConfig", "FinanceConfig", "AppConfig"]