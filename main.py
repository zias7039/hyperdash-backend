import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import services
from services.bitget import fetch_positions, fetch_account
from services.upbit import fetch_usdt_krw
from services.history import try_record_snapshot, load_history
from services.fund import get_nav_metrics
from utils.format import fnum

# Load environment variables
load_dotenv()

app = FastAPI(title="Hyperdash API", version="1.0.0")

# Enable CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any origin (including your future Vercel domain)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config constants (from app.py)
PRODUCT_TYPE = "USDT-FUTURES"
MARGIN_COIN = "USDT"

def get_bitget_credentials():
    api_key = os.getenv("BITGET_API_KEY")
    api_secret = os.getenv("BITGET_API_SECRET")
    passphrase = os.getenv("BITGET_PASSPHRASE")
    
    if not all([api_key, api_secret, passphrase]):
        raise HTTPException(status_code=500, detail="Bitget credentials not configured in environment.")
        
    return api_key, api_secret, passphrase

@app.get("/api/dashboard")
async def get_dashboard_data():
    api_key, api_secret, passphrase = get_bitget_credentials()
    
    try:
        # Fetch data
        pos_data, _ = fetch_positions(api_key, api_secret, passphrase, PRODUCT_TYPE, MARGIN_COIN)
        acct_data, _ = fetch_account(api_key, api_secret, passphrase, PRODUCT_TYPE, MARGIN_COIN)
        usdt_rate = fetch_usdt_krw()
        
        # Metrics Calc
        available = fnum(acct_data.get("available")) if acct_data else 0.0
        equity = fnum(acct_data.get("usdtEquity")) if acct_data else available
        
        upl_pnl = sum(fnum(p.get("unrealizedPL", 0)) for p in pos_data)
        margin_used = sum(fnum(p.get("marginSize", 0)) for p in pos_data)
        
        roe = (upl_pnl / equity * 100) if equity > 0 else 0
        usage_pct = (margin_used / equity * 100) if equity > 0 else 0
        
        leverage = 0
        if equity > 0:
            leverage = sum(fnum(p.get("marginSize", 0)) * fnum(p.get("leverage", 0)) for p in pos_data) / equity
            
        # Try to record snapshot
        history_df, _ = try_record_snapshot(equity)
        
        # Get NAV Data
        nav_data = get_nav_metrics(equity, history_df)
        
        # Convert History DataFrame to list of dicts for JSON response
        history_list = history_df.to_dict('records')
        
        # Fetch BTC Benchmark Current
        from services.bitget import fetch_btc_ticker, fetch_kline_futures
        btc_ticker = fetch_btc_ticker()
        btc_price = fnum(btc_ticker.get("lastPr", 0))
        btc_change_24h = fnum(btc_ticker.get("chgUtc", btc_ticker.get("changeUtc24h", 0))) * 100
        
        # [NEW] Fetch BTC Historical Data (1D candles) to match with history_df dates
        btc_history = []
        if not history_df.empty:
            try:
                # Fetch recent daily candles (adjust limit if history is longer than 100 days)
                btc_df = fetch_kline_futures(symbol="BTCUSDT", granularity="1D", limit=100)
                if not btc_df.empty:
                    # Format BTC timestamp to YYYY-MM-DD
                    btc_df['date'] = btc_df['timestamp'].dt.strftime('%Y-%m-%d')
                    # Create a dictionary for fast lookup: { 'YYYY-MM-DD': close_price }
                    btc_price_map = dict(zip(btc_df['date'], btc_df['close']))
                    
                    # Align BTC price to user's equity history
                    first_btc_price = None
                    first_equity = fnum(history_list[0]['equity']) if history_list else 0
                    
                    for item in history_list:
                        date_str = item['date']
                        b_price = btc_price_map.get(date_str)
                        if b_price:
                            if first_btc_price is None:
                                first_btc_price = b_price
                                
                            item['btc_price'] = b_price
                            # Calculate normalized BTC NAV (same starting point as equity)
                            if first_equity > 0:
                                item['btc_nav'] = first_equity * (b_price / first_btc_price)
                            else:
                                item['btc_nav'] = b_price # fallback
                        else:
                            # If no exact date match, carry forward previous or set None
                            item['btc_price'] = None
                            item['btc_nav'] = None
            except Exception as e:
                print(f"Error fetching historical BTC: {e}")
        
        return {
            "metrics": {
                "equity": equity,
                "available": available,
                "leverage": leverage,
                "usage_pct": usage_pct,
                "upl_pnl": upl_pnl,
                "roe": roe,
                "usdt_rate": usdt_rate
            },
            "positions": pos_data,
            "nav_data": nav_data,
            "history": history_list,
            "btc_benchmark": {
                "price": btc_price,
                "change24h": btc_change_24h
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")

@app.post("/api/dashboard/snapshot")
async def force_snapshot():
    api_key, api_secret, passphrase = get_bitget_credentials()
    try:
        acct_data, _ = fetch_account(api_key, api_secret, passphrase, PRODUCT_TYPE, MARGIN_COIN)
        available = fnum(acct_data.get("available")) if acct_data else 0.0
        equity = fnum(acct_data.get("usdtEquity")) if acct_data else available
        
        _, recorded = try_record_snapshot(equity, force=True)
        return {"success": True, "recorded": recorded, "equity": equity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forcing snapshot: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
