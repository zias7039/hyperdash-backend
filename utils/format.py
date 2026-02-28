# utils/format.py

def fnum(v):
    try: return float(v)
    except: return 0.0

def safe_pct(num, den):
    return (num/den*100.0) if den else 0.0

def normalize_symbol(sym: str) -> str:
    return (sym or "").split("_")[0].upper()

