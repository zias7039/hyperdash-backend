import json
import pandas as pd
import os
from dotenv import load_dotenv

# load environment variables before importing services
load_dotenv()

from services.db import init_db
from services.history import update_bulk_history
from utils.settings import save_settings

def migrate():
    # Initialize the database
    init_db()
    
    # Migrate Settings
    print("Migrating settings...")
    if os.path.exists("data/settings.json"):
        with open("data/settings.json", "r") as f:
            old_settings = json.load(f)
            save_settings(old_settings)
            print("Settings migrated:", old_settings)
    else:
        print("No settings to migrate.")

    # Migrate History
    print("Migrating history...")
    if os.path.exists("data/equity_history.csv"):
        df = pd.read_csv("data/equity_history.csv")
        records = df.to_dict(orient="records")
        # Format the dictionaries expected by the bulk history function
        success = update_bulk_history(records)
        print("History migration success:", success, "Records migrated:", len(records))
    else:
        print("No history to migrate.")

if __name__ == "__main__":
    migrate()
