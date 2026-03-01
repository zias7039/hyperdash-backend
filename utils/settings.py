import json
import os

SETTINGS_FILE = "data/settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"total_invested": 0.0}
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"total_invested": 0.0}

def save_settings(settings: dict):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
