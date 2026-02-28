import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from services.bitget import fetch_kline_futures

df = fetch_kline_futures(symbol="BTCUSDT", granularity="1d", limit=1000)
if not df.empty:
    df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    print("Found dates 1d:", len(df))
    print("First date 1d:", df['date'].iloc[0])
    print("Last date 1d:", df['date'].iloc[-1])
else:
    print("No data for 1d")

df2 = fetch_kline_futures(symbol="BTCUSDT", granularity="1D", limit=1000)
if not df2.empty:
    df2['date'] = df2['timestamp'].dt.strftime('%Y-%m-%d')
    print("Found dates 1D:", len(df2))
    print("First date 1D:", df2['date'].iloc[0])
    print("Last date 1D:", df2['date'].iloc[-1])
else:
    print("No data for 1D")
