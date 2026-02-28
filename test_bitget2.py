import sys
import os
import requests
import pandas as pd
sys.path.insert(0, os.path.abspath('.'))

BASE_URL = "https://api.bitget.com"

def fetch_history(symbol="BTCUSDT", granularity="1D", limit=1000):
    try:
        path = "/api/v2/mix/market/history-candles"
        end_time = "" # current time
        params = {
            "symbol": symbol,
            "granularity": granularity,
            "productType": "USDT-FUTURES",
            # "limit": str(limit) # history-candles might require start/end or limit
        }
        res = requests.get(f"{BASE_URL}{path}", params=params, timeout=5).json()
        print(res)
        return res
    except Exception as e:
        print(e)

fetch_history()
