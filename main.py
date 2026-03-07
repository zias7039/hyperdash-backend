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

from apscheduler.schedulers.asyncio import AsyncIOScheduler

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

# --- APScheduler Background Task ---
scheduler = AsyncIOScheduler()

async def auto_record_snapshot_task():
    try:
        api_key, api_secret, passphrase = get_bitget_credentials()
        # Run synchronous network calls in a thread if blocking, or just direct if simple
        import asyncio
        acct_data, _ = await asyncio.to_thread(fetch_account, api_key, api_secret, passphrase, PRODUCT_TYPE, MARGIN_COIN)
        available = fnum(acct_data.get("available")) if acct_data else 0.0
        equity = fnum(acct_data.get("usdtEquity")) if acct_data else available
        
        _, recorded = await asyncio.to_thread(try_record_snapshot, equity, True) # force=True
        
        if recorded:
            try:
                from services.telegram import send_telegram_message
                import datetime
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                msg = f"⏱️ <b>Hyperdash Auto Daily Snapshot</b> ({date_str})\n\n"
                msg += f"💰 <b>Total Equity:</b> ${equity:,.2f}"
                send_telegram_message(msg)
            except Exception:
                pass
            print(f"Auto snapshot recorded successfully at {equity}")
            
    except Exception as e:
        print(f"Error in auto snapshot task: {e}")

@app.on_event("startup")
def start_scheduler():
    from services.db import init_db
    init_db()
    
    # Schedule to run every day at 09:00 AM KST
    scheduler.add_job(auto_record_snapshot_task, 'cron', hour=9, minute=0, timezone='Asia/Seoul')
    scheduler.start()
    print("APScheduler started. Snapshot scheduled for 09:00 AM KST.")

@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()

@app.get("/api/dashboard")
async def get_dashboard_data():
    api_key, api_secret, passphrase = get_bitget_credentials()
    
    try:
        import asyncio
        from services.bitget import fetch_btc_ticker
        import requests

        # Define async wrappers for our synchronous functions
        async def fetch_pos():
            return await asyncio.to_thread(fetch_positions, api_key, api_secret, passphrase, PRODUCT_TYPE, MARGIN_COIN)
        
        async def fetch_acc():
            return await asyncio.to_thread(fetch_account, api_key, api_secret, passphrase, PRODUCT_TYPE, MARGIN_COIN)
        
        async def fetch_rate():
            return await asyncio.to_thread(fetch_usdt_krw)
            
        async def fetch_btc():
            return await asyncio.to_thread(fetch_btc_ticker)
            
        async def fetch_btc_klines():
            """Fetch BTC daily prices - Bitget first (guaranteed to work from Render), then fallbacks"""
            def _fetch():
                # Try Bitget spot klines first (same API provider, guaranteed to work)
                try:
                    bg_url = "https://api.bitget.com/api/v2/spot/market/candles"
                    bg_params = {"symbol": "BTCUSDT", "granularity": "1day", "limit": "200"}
                    bg_res = requests.get(bg_url, params=bg_params, timeout=10)
                    if bg_res.status_code == 200:
                        bg_data = bg_res.json()
                        if bg_data.get("code") == "00000":
                            candles = bg_data.get("data", [])
                            # Bitget format: [timestamp, open, high, low, close, volume, ...]
                            # Convert to unified format: [timestamp_ms, open, high, low, close]
                            result = []
                            for c in candles:
                                result.append([int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4])])
                            return result
                except Exception as e:
                    print(f"Bitget klines failed: {e}")
                
                # Fallback to CoinGecko
                try:
                    cg_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
                    cg_params = {"vs_currency": "usd", "days": "365", "interval": "daily"}
                    cg_res = requests.get(cg_url, params=cg_params, timeout=10)
                    if cg_res.status_code == 200:
                        prices = cg_res.json().get("prices", [])
                        return [[p[0], 0, 0, 0, p[1]] for p in prices]
                except Exception as e:
                    print(f"CoinGecko failed: {e}")
                
                # Fallback to Binance
                try:
                    res = requests.get("https://api.binance.com/api/v3/klines", params={
                        "symbol": "BTCUSDT", "interval": "1d", "limit": 1000
                    }, timeout=5)
                    return res.json()
                except Exception as e:
                    print(f"Binance also failed: {e}")
                    return []
            return await asyncio.to_thread(_fetch)

        # Run all external requests concurrently
        pos_result, acct_result, usdt_rate, btc_ticker, binance_res = await asyncio.gather(
            fetch_pos(),
            fetch_acc(),
            fetch_rate(),
            fetch_btc(),
            fetch_btc_klines(),
            return_exceptions=True
        )
        
        # Unpack results handling potential exceptions
        pos_data = pos_result[0] if not isinstance(pos_result, Exception) else []
        acct_data = acct_result[0] if not isinstance(acct_result, Exception) else None
        usdt_rate = usdt_rate if not isinstance(usdt_rate, Exception) else None
        btc_ticker = btc_ticker if not isinstance(btc_ticker, Exception) else {}
        
        binance_err = str(binance_res) if isinstance(binance_res, Exception) else None
        binance_res = binance_res if not isinstance(binance_res, Exception) else []

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
            
        # Margin Distribution Calc
        margin_dist = {}
        for p in pos_data:
            sym = p.get("symbol", "").replace("USDT", "")
            if sym and fnum(p.get("marginSize", 0)) > 0:
                margin_dist[sym] = margin_dist.get(sym, 0) + fnum(p.get("marginSize", 0))
        
        margin_distribution = [{"name": k, "value": v} for k, v in margin_dist.items()]
        margin_distribution.sort(key=lambda x: x["value"], reverse=True)
            
        # Try to record snapshot
        history_df, _ = await asyncio.to_thread(try_record_snapshot, equity)
        
        # Get NAV Data
        nav_data = await asyncio.to_thread(get_nav_metrics, equity, history_df)
        
        # Convert History DataFrame to list of dicts for JSON response
        history_list = history_df.to_dict('records')
        
        # Calculate daily PnL
        prev_equity = None
        for item in history_list:
            eq = fnum(item['equity'])
            if prev_equity is not None:
                item['daily_pnl'] = eq - prev_equity
            else:
                item['daily_pnl'] = 0
            prev_equity = eq
        
        btc_price = fnum(btc_ticker.get("lastPr", 0))
        btc_change_24h = fnum(btc_ticker.get("chgUtc", btc_ticker.get("changeUtc24h", 0))) * 100
        
        # [NEW] Fetch BTC Historical Data (1D candles) to match with history_df dates
        btc_history = []
        if not history_df.empty:
            if binance_res and isinstance(binance_res, list) and len(binance_res) > 0:
                import datetime
                # Create a dictionary for fast lookup: { 'YYYY-MM-DD': close_price }
                btc_price_map = {}
                for candle in binance_res:
                    try:
                        d_str = datetime.datetime.fromtimestamp(int(candle[0])/1000).strftime('%Y-%m-%d')
                        btc_price_map[d_str] = float(candle[4]) # index 4 is close price
                    except (ValueError, TypeError, IndexError):
                        continue
                    
                # Align BTC price to user's equity history
                first_btc_price = None
                first_equity = fnum(history_list[0]['equity']) if history_list else 0
                last_known_bp = None
                
                for item in history_list:
                    raw_date = item['date']
                    # Handle both strings and datetime/Timestamp objects
                    date_val = str(raw_date)[:10] if raw_date else ""
                    
                    b_price = btc_price_map.get(date_val)
                    if b_price:
                        if first_btc_price is None:
                            first_btc_price = b_price
                            
                        item['btc_price'] = b_price
                        last_known_bp = b_price
                        # Calculate normalized BTC NAV (same starting point as equity)
                        if first_equity > 0:
                            item['btc_nav'] = first_equity * (b_price / first_btc_price)
                        else:
                            item['btc_nav'] = b_price # fallback
                    else:
                        # If no exact date match, carry forward previous
                        item['btc_price'] = last_known_bp
                        if last_known_bp and first_btc_price:
                            item['btc_nav'] = first_equity * (last_known_bp / first_btc_price)
                        else:
                            item['btc_nav'] = None
        
        # ===== Deposit-Aware Return Rate Calculation =====
        from services.deposits import load_deposits
        deposits = load_deposits()
        
        if deposits and history_list:
            # Sort deposits by date for chronological processing
            sorted_deposits = sorted(deposits, key=lambda x: x["date"])
            
            # Calculate cumulative invested capital at each history date
            cumulative_invested = 0
            dep_idx = 0
            
            for item in history_list:
                raw_date = item["date"]
                date_str = str(raw_date)[:10] if raw_date else ""
                
                # Apply all deposits that happened on or before this history date
                while dep_idx < len(sorted_deposits) and sorted_deposits[dep_idx]["date"] <= date_str:
                    dep = sorted_deposits[dep_idx]
                    amt = dep["amount"]
                    if dep["type"] == "withdrawal":
                        amt = -amt
                    cumulative_invested += amt
                    dep_idx += 1
                
                item["invested_capital"] = round(cumulative_invested, 2)
                eq = fnum(item["equity"])
                if cumulative_invested > 0:
                    item["return_pct"] = round(((eq - cumulative_invested) / cumulative_invested) * 100, 2)
                else:
                    item["return_pct"] = 0
            
            # Also compute BTC return % over same period (aligned with deposits)
            first_btc = None
            for item in history_list:
                # Start tracking BTC return only when we have invested capital
                if item.get("invested_capital", 0) > 0:
                    bp = item.get("btc_price")
                    if bp and bp > 0:
                        if first_btc is None:
                            first_btc = bp
                        item["btc_return_pct"] = round(((bp - first_btc) / first_btc) * 100, 2)
                    else:
                        item["btc_return_pct"] = None
                else:
                    item["btc_return_pct"] = None
        
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
            "margin_distribution": margin_distribution,
            "btc_benchmark": {
                "price": btc_price,
                "change24h": btc_change_24h,
                "binance_error": binance_err
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
        
        if recorded:
            from services.telegram import send_telegram_message
            import datetime
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            msg = f"📊 <b>Hyperdash Daily Report</b> ({date_str})\n\n"
            msg += f"💰 <b>Total Equity:</b> ${equity:,.2f}"
            send_telegram_message(msg)

        return {"success": True, "recorded": recorded, "equity": equity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forcing snapshot: {str(e)}")

# --- User Inputs & Settings APIs ---

from utils.settings import load_settings, save_settings
from services.history import insert_manual_history

class SettingsUpdate(BaseModel):
    total_invested: float

@app.get("/api/settings")
async def get_settings():
    return load_settings()

@app.post("/api/settings")
async def update_settings(data: SettingsUpdate):
    try:
        settings = load_settings()
        settings["total_invested"] = data.total_invested
        save_settings(settings)
        return {"success": True, "total_invested": data.total_invested}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from typing import List

class HistoryUpdate(BaseModel):
    date: str
    equity: float

@app.post("/api/history")
async def update_history(data: HistoryUpdate):
    try:
        success = insert_manual_history(data.date, data.equity)
        return {"success": success, "date": data.date, "equity": data.equity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/history/bulk")
async def update_history_bulk(data: List[HistoryUpdate]):
    try:
        from services.history import update_bulk_history
        data_list = [{"date": item.date, "equity": item.equity} for item in data]
        success = update_bulk_history(data_list)
        return {"success": success, "count": len(data_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DepositUpdate(BaseModel):
    date: str
    type: str # 'deposit' or 'withdrawal'
    amount: float

@app.get("/api/deposits")
async def get_deposits_api():
    from services.deposits import load_deposits
    return load_deposits()

@app.post("/api/deposits")
async def update_deposits_bulk(data: List[DepositUpdate]):
    try:
        from services.deposits import update_bulk_deposits
        data_list = [{"date": item.date, "type": item.type, "amount": item.amount} for item in data]
        success = update_bulk_deposits(data_list)
        return {"success": success, "count": len(data_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
