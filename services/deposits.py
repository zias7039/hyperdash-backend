import uuid
from services import db as db_module
from services.db import DepositHistory

def load_deposits():
    if not db_module.SessionLocal:
        return []
    db = db_module.SessionLocal()
    try:
        records = db.query(DepositHistory).order_by(DepositHistory.date.asc()).all()
        result = []
        for r in records:
            result.append({
                "id": r.id,
                "date": r.date,
                "type": r.type,
                "amount": float(r.amount)
            })
        return result
    except Exception:
        return []
    finally:
        db.close()

def update_bulk_deposits(data_list: list):
    if not db_module.SessionLocal:
        return False
    db = db_module.SessionLocal()
    try:
        # For bulk updates in this simple dashboard, we replace everything
        # Just clear existing deposits and insert the passed list
        db.query(DepositHistory).delete()
        
        for item in data_list:
            record = DepositHistory(
                id=str(uuid.uuid4()),
                date=item["date"],
                type=item["type"],
                amount=float(item["amount"])
            )
            db.add(record)
            
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()
