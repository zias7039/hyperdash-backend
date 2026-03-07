from services.db import SessionLocal, Setting

def load_settings():
    if not SessionLocal:
        return {"total_invested": 0.0}
    db = SessionLocal()
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
    if not SessionLocal:
        return
    db = SessionLocal()
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
