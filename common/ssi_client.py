import os
import requests
import pandas as pd
from config import ssi_config, app_config

def get_ssi_access_token() -> str | None:
    """Lấy Access Token từ SSI FastConnect Data API v2."""
    if not ssi_config.is_configured:
        return None
        
    url = f"{ssi_config.base_url}/AccessToken"
    payload = {
        "consumerID": ssi_config.consumer_id,
        "consumerSecret": ssi_config.consumer_secret
    }
    try:
        res = requests.post(url, json=payload, timeout=ssi_config.timeout)
        if res.status_code == 200:
            return res.json().get("data", {}).get("accessToken")
    except Exception as e:
        print(f"Lỗi lấy Token SSI: {e}")
    return None

def fetch_company_financial_ratio(symbol: str) -> tuple[pd.DataFrame, str, bool]:
    """
    Hàm lấy BCTC & Chỉ số tài chính cho các Module 2/3/5.
    Trả về: (DataFrame dữ liệu, Tên nguồn dữ liệu, cờ is_mock)
    """
    # 1. Thử gọi Endpoint SSI
    token = get_ssi_access_token()
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{ssi_config.base_url}{ssi_config.financial_endpoint}"
        try:
            res = requests.get(url, headers=headers, params={"symbol": symbol}, timeout=ssi_config.timeout)
            if res.status_code == 200 and res.json().get("data"):
                return pd.DataFrame(res.json()["data"]), "SSI FastConnect", False
        except Exception:
            pass

    # 2. Thay thế bằng Vnstock (Dữ liệu THẬT) nếu SSI Endpoint BCTC bị chặn/lỗi
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol=symbol, source='VND')
        df_ratios = stock.finance.ratio(period='quarter', lang='vi')
        
        if df_ratios is not None and not df_ratios.empty:
            return df_ratios, "SSI + Vnstock (Real Data)", False
    except Exception as e:
        print(f"Lỗi Fallback Vnstock: {e}")

    # 3. Chỉ trả về Mock nếu app_config.use_mock = True
    if app_config.use_mock:
        return pd.DataFrame(), "MOCK", True

    return pd.DataFrame(), "Không có dữ liệu", False