import pandas as pd
from datetime import datetime, timedelta, timezone
from services.db import engine, SessionLocal, EquityHistory

def get_kst_now():
    return datetime.now(timezone(timedelta(hours=9)))

def load_history():
    if not engine:
        return pd.DataFrame(columns=["date", "equity"])
    try:
        df = pd.read_sql("SELECT * FROM equity_history ORDER BY date ASC", con=engine)
        return df
    except Exception:
        return pd.DataFrame(columns=["date", "equity"])

# [수정됨] force=True일 경우 조건 무시하고 저장
def try_record_snapshot(current_equity, force=False):
    df = load_history()
    now_kst = get_kst_now()
    today_str = now_kst.strftime("%Y-%m-%d")

    is_exist = today_str in df["date"].values

    if (not is_exist and now_kst.hour >= 9) or force:
        if not SessionLocal:
            return df, False
        db = SessionLocal()
        try:
            record = db.query(EquityHistory).filter(EquityHistory.date == today_str).first()
            if record:
                record.equity = float(current_equity)
            else:
                record = EquityHistory(date=today_str, equity=float(current_equity))
                db.add(record)
            db.commit()
            return load_history(), True
        except Exception:
            db.rollback()
            return df, False
        finally:
            db.close()
            
    return df, False

def insert_manual_history(date_str: str, equity_value: float):
    if not SessionLocal:
        return False
    db = SessionLocal()
    try:
        record = db.query(EquityHistory).filter(EquityHistory.date == date_str).first()
        if record:
            record.equity = float(equity_value)
        else:
            record = EquityHistory(date=date_str, equity=float(equity_value))
            db.add(record)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def update_bulk_history(data_list: list):
    if not SessionLocal:
        return False
    db = SessionLocal()
    try:
        for item in data_list:
            date_str = item["date"]
            equity_value = item["equity"]
            record = db.query(EquityHistory).filter(EquityHistory.date == date_str).first()
            if record:
                record.equity = float(equity_value)
            else:
                record = EquityHistory(date=date_str, equity=float(equity_value))
                db.add(record)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()
