# services/history.py
import os
import pandas as pd
from datetime import datetime, timedelta, timezone

DATA_DIR = "data"
FILE_PATH = os.path.join(DATA_DIR, "equity_history.csv")

def get_kst_now():
    return datetime.now(timezone(timedelta(hours=9)))

def load_history():
    if not os.path.exists(FILE_PATH):
        return pd.DataFrame(columns=["date", "equity"])
    try:
        df = pd.read_csv(FILE_PATH)
        return df
    except Exception:
        return pd.DataFrame(columns=["date", "equity"])

# [수정됨] force=True일 경우 조건 무시하고 저장
def try_record_snapshot(current_equity, force=False):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    df = load_history()
    now_kst = get_kst_now()
    today_str = now_kst.strftime("%Y-%m-%d")

    # 이미 오늘 데이터가 있는지 확인
    is_exist = today_str in df["date"].values

    # 조건 1: 오늘 기록이 없고 & 9시가 지났거나
    # 조건 2: 강제 저장(force) 버튼을 눌렀을 때
    if (not is_exist and now_kst.hour >= 9) or force:
        
        # 만약 강제 저장인데 오늘 날짜가 이미 있다면 -> 덮어쓰기 위해 기존 행 삭제
        if force and is_exist:
            df = df[df["date"] != today_str]

        new_row = pd.DataFrame([{"date": today_str, "equity": current_equity}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(FILE_PATH, index=False)
        return df, True # 저장됨
        
    return df, False

def insert_manual_history(date_str: str, equity_value: float):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    df = load_history()
    
    # Remove existing record if it exists
    if date_str in df["date"].values:
        df = df[df["date"] != date_str]
        
    # Append new record
    new_row = pd.DataFrame([{"date": date_str, "equity": equity_value}])
    df = pd.concat([df, new_row], ignore_index=True)
    
    # Sort by date so chart stays correct
    df = df.sort_values(by="date", ascending=True)
    
    df.to_csv(FILE_PATH, index=False)
    return True
