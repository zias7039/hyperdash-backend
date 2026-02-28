# services/upbit.py
import requests
import streamlit as st

@st.cache_data(ttl=60)
def fetch_usdt_krw() -> float | None:
    try:
        # 업비트 KRW-USDT 마켓 직접 조회
        res = requests.get(
            "https://api.upbit.com/v1/ticker",
            params={"markets": "KRW-USDT"},
            timeout=5
        )
        data = res.json()
        
        # 데이터가 정상적으로 오면 현재가(trade_price) 반환
        if data and isinstance(data, list):
            return float(data[0]["trade_price"])
            
    except Exception:
        pass
    
    return None
