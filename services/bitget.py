# services/bitget.py
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
from urllib.parse import urlencode
from typing import Optional, Tuple, List, Dict, Any

BASE_URL = "https://api.bitget.com"

def _timestamp_ms() -> str:
    return str(int(time.time() * 1000))

def _sign(ts: str, method: str, path: str, query_params: Optional[Dict], body: str, secret: str) -> str:
    body = body or ""
    method_up = method.upper()
    q = urlencode(query_params) if query_params else ""
    target = f"{ts}{method_up}{path}?{q}{body}" if query_params else f"{ts}{method_up}{path}{body}"
    
    mac = hmac.new(secret.encode(), target.encode(), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def _private_get(api_key: str, api_secret: str, passphrase: str, path: str, params: Optional[Dict] = None) -> Dict:
    try:
        ts = _timestamp_ms()
        sig = _sign(ts, "GET", path, params, "", api_secret)
        
        query_str = f"?{urlencode(params)}" if params else ""
        url = f"{BASE_URL}{path}{query_str}"
        
        headers = {
            "ACCESS-KEY": api_key,
            "ACCESS-SIGN": sig,
            "ACCESS-PASSPHRASE": passphrase,
            "ACCESS-TIMESTAMP": ts,
            "locale": "en-US",
            "Content-Type": "application/json",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        return {"code": "99999", "msg": f"Network Error: {str(e)}", "data": None}

def fetch_positions(api_key: str, api_secret: str, passphrase: str, product_type: str, margin_coin: str) -> Tuple[List[Dict], Dict]:
    res = _private_get(api_key, api_secret, passphrase,
                       "/api/v2/mix/position/all-position",
                       {"productType": product_type, "marginCoin": margin_coin})
    return (res.get("data") or [], res)

def fetch_account(api_key: str, api_secret: str, passphrase: str, product_type: str, margin_coin: str) -> Tuple[Optional[Dict], Dict]:
    res = _private_get(api_key, api_secret, passphrase,
                       "/api/v2/mix/account/accounts",
                       {"productType": product_type, "marginCoin": margin_coin})
    arr = res.get("data") or []
    acct = next((a for a in arr if a.get("marginCoin") == margin_coin), None)
    return acct, res

def fetch_account_bills(api_key: str, api_secret: str, passphrase: str, product_type: str, limit: int = 100) -> List[Dict]:
    res = _private_get(api_key, api_secret, passphrase,
                       "/api/v2/mix/account/bill",
                       {"productType": product_type, "limit": str(limit)})
    data_obj = res.get("data", {}) if res.get("data") else {}
    return data_obj.get("bills", [])

def fetch_kline_futures(symbol: str = "BTCUSDT", granularity: str = "1h", product_type: str = "USDT-FUTURES", limit: int = 100) -> pd.DataFrame:
    """
    선물(Mix) 캔들 데이터 조회 (V2)
    """
    try:
        path = "/api/v2/mix/market/candles"
        params = {
            "symbol": symbol,
            "granularity": granularity,
            "productType": product_type,
            "limit": str(limit)
        }
        res = requests.get(f"{BASE_URL}{path}", params=params, timeout=5).json()
        
        if res.get("code") != "00000": 
            return pd.DataFrame()
            
        data = res.get("data", [])
        if not data: 
            return pd.DataFrame()
        
        # [timestamp, open, high, low, close, vol, amount]
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "vol", "amount"])
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(float), unit="ms")
        
        # 형변환
        numeric_cols = ["open", "high", "low", "close"]
        df[numeric_cols] = df[numeric_cols].astype(float)
        
        return df.sort_values("timestamp")
    except Exception:
        return pd.DataFrame()
