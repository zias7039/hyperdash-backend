# services/fund.py
import json
import os
from typing import Dict, Any

DATA_FILE = "data/fund_state.json"

def load_fund_state() -> Dict[str, Any]:
    """
    투자자별 Units 정보를 불러옵니다.
    파일이 없거나 구버전일 경우, 초기 투자자(Investor A/B) 상태를 반환합니다.
    """
    # [수정] 주석과 코드의 초기값 통일 (A: 754, B: 265)
    default_state = {
        "investors": {
            "Investor A": 1624.0,
            "Investor B": 1.0
        }
    }

    if not os.path.exists(DATA_FILE):
        return default_state
    
    try:
        with open(DATA_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            if "investors" not in data:
                return default_state
            return data
    except Exception as e:
        print(f"Error loading fund state: {e}")
        return default_state

def save_fund_state(investors_dict: Dict[str, float]) -> None:
    """투자자별 현황 저장"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding='utf-8') as f:
        json.dump({"investors": investors_dict}, f, indent=2, ensure_ascii=False)

def get_nav_metrics(current_equity: float, history_df) -> Dict[str, Any]:
    """NAV, 변동률, 그리고 투자자별 평가액 계산"""
    state = load_fund_state()
    investors = state.get("investors", {})
    
    total_units = sum(investors.values())
    if total_units <= 0: 
        total_units = 1.0
        
    current_nav = current_equity / total_units
    
    # NAV 변동률 (전일 대비)
    nav_change_pct = 0.0
    if not history_df.empty:
        last_equity = history_df["equity"].iloc[-1]
        if last_equity > 0:
            nav_change_pct = ((current_equity - last_equity) / last_equity) * 100.0
            
    return {
        "nav": current_nav,
        "total_units": total_units,
        "change_pct": nav_change_pct,
        "investors": investors
    }
