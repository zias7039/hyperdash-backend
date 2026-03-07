import json
import os
import uuid
from dotenv import load_dotenv

load_dotenv()
from services.db import init_db
from services import db as db_module
from services.db import DepositHistory

def migrate_deposits():
    init_db()
    
    file_path = "data/deposits.json"
    if not os.path.exists(file_path):
        print(f"No deposits file found at {file_path}")
        return
        
    with open(file_path, "r") as f:
        deposits = json.load(f)
        
    db = db_module.SessionLocal()
    try:
        count = 0
        for dep in deposits:
            record_id = str(uuid.uuid4())
            record = DepositHistory(
                id=record_id,
                date=dep["date"],
                type=dep["type"],
                amount=float(dep["amount"])
            )
            db.add(record)
            count += 1
            
        db.commit()
        print(f"Successfully migrated {count} deposit records to the database.")
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_deposits()
