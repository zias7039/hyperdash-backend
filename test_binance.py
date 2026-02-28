import requests
res = requests.get("https://api.binance.com/api/v3/klines", params={"symbol": "BTCUSDT", "interval": "1d", "limit": 1000}).json()
print("Binance 1d candles:", len(res))
if len(res) > 0:
    import datetime
    d0 = datetime.datetime.fromtimestamp(res[0][0]/1000).strftime('%Y-%m-%d')
    d1 = datetime.datetime.fromtimestamp(res[-1][0]/1000).strftime('%Y-%m-%d')
    print("Start:", d0, "End:", d1)
