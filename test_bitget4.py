import sys
import os
import requests

from services.bitget import fetch_kline_futures

BASE_URL = "https://api.bitget.com"

# test history-candles with just limit=1000
path = "/api/v2/mix/market/history-candles"
params = {
    "symbol": "BTCUSDT",
    "granularity": "1D",
    "productType": "USDT-FUTURES",
    "limit": "1000"
}
res = requests.get(f"{BASE_URL}{path}", params=params, timeout=5).json()
data = res.get("data", [])
if data:
    print("history-candles returned:", len(data))
    print(data[0]) 
    print(data[-1])
else:
    print("history-candles returned no data or error:", res)
