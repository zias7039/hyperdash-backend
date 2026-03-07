from services.db import Setting
from services import db as db_module

def load_settings():
    if not db_module.SessionLocal:
        return {"total_invested": 0.0}
    db = db_module.SessionLocal()
    try:
        record = db.query(Setting).filter(Setting.key == "total_invested").first()
        if record:
            return {"total_invested": float(record.value)}
        return {"total_invested": 0.0}
    except Exception:
        return {"total_invested": 0.0}
    finally:
        db.close()

def save_settings(settings: dict):
    if not db_module.SessionLocal:
        return
    db = db_module.SessionLocal()
    try:
        val = settings.get("total_invested", 0.0)
        record = db.query(Setting).filter(Setting.key == "total_invested").first()
        if record:
            record.value = float(val)
        else:
            record = Setting(key="total_invested", value=float(val))
            db.add(record)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
