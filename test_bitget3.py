import sys
import os
import requests
import datetime
sys.path.insert(0, os.path.abspath('.'))

BASE_URL = "https://api.bitget.com"

def fetch_history(symbol="BTCUSDT", granularity="1D", limit=100) -> list:
    try:
        path = "/api/v2/mix/market/history-candles"
        end_time = int(datetime.datetime.now().timestamp() * 1000)
        start_time = end_time - (limit * 24 * 60 * 60 * 1000)
        params = {
            "symbol": symbol,
            "granularity": granularity,
            "productType": "USDT-FUTURES",
            "endTime": str(end_time),
            "startTime": str(start_time),
            "limit": "100" # Max string limit? Let's check docs. Usually 100, we might need pagination
        }
        res = requests.get(f"{BASE_URL}{path}", params=params, timeout=5).json()
        data = res.get("data", [])
        print("Data length:", len(data))
        if data:
            d0 = datetime.datetime.fromtimestamp(int(data[0][0])/1000).strftime('%Y-%m-%d')
            d1 = datetime.datetime.fromtimestamp(int(data[-1][0])/1000).strftime('%Y-%m-%d')
            print("First date:", d0, "Last date:", d1)
        return res
    except Exception as e:
        print(e)

fetch_history(limit=400)
