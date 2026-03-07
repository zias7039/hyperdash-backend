from dotenv import load_dotenv
load_dotenv()
from services.db import init_db
from utils.settings import load_settings
from services.history import load_history

init_db()
s = load_settings()
print(f"Loaded total_invested: {s}")

h = load_history()
print(f"Loaded history records: {len(h)}")
if len(h) > 0:
    print("Sample:", h.iloc[-1].to_dict())
