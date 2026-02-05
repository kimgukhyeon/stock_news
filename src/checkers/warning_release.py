import pandas as pd
from datetime import datetime

def check_release_conditions(df: pd.DataFrame, target_idx: int):
    """
    Checks if the stock meets the investment warning release conditions on a specific trading day.
    
    Conditions for release (must NOT meet any of these to be released):
    1. T의 종가가 5일 전날(T-5)의 종가보다 60% 이상 상승
    2. T의 종가가 15일 전날(T-15)의 종가보다 100% 이상 상승
    3. T의 종가가 최근 15일 종가 중 최고가 (T일 포함, T-14 ~ T)
    """
    if target_idx < 15:
        return False, None

    current_price = df.iloc[target_idx]['Close']
    t_minus_5_price = df.iloc[target_idx - 5]['Close']
    t_minus_15_price = df.iloc[target_idx - 15]['Close']
    
    # Condition 3: Max of previous 14 days + current day (total 15 days)
    # The rule says "current price is NOT the highest among last 15 days"
    # So we check if current price is >= max of the others, or simply if it's the max of the 15-day window.
    recent_15_prices = df.iloc[target_idx-14 : target_idx+1]['Close']
    max_price_15 = recent_15_prices.max()
    
    thresh_5d = t_minus_5_price * 1.6
    thresh_15d = t_minus_15_price * 2.0
    thresh_max = max_price_15
    
    # To be released, current price must be LESS THAN all these thresholds.
    # Note: If current price IS the max, it fails release. 
    # Technically, condition 3 is "current price is the highest".
    # We check if it is NOT the highest.
    
    is_highest = (current_price >= recent_15_prices.iloc[:-1].max()) if len(recent_15_prices) > 1 else True
    # Wait, usually "is the highest" means current_price == max(window).
    is_highest = current_price >= recent_15_prices.max()

    cond1_fail = current_price >= thresh_5d
    cond2_fail = current_price >= thresh_15d
    cond3_fail = is_highest
    
    can_release = not (cond1_fail or cond2_fail or cond3_fail)
    
    # Calculating the "Max Price for Release" (The lowest of the three thresholds)
    # Price must be strictly LESS than these to not trigger the "fail" condition.
    # For condition 3, it must be less than the max of the PREVIOUS 14 days.
    prev_14_max = recent_15_prices.iloc[:-1].max()
    
    release_ceiling = min(thresh_5d, thresh_15d, prev_14_max)
    
    details = {
        "date": df.index[target_idx].strftime('%Y-%m-%d'),
        "close": current_price,
        "release_ceiling": release_ceiling,
        "thresh_5d": thresh_5d,
        "thresh_15d": thresh_15d,
        "prev_14_max": prev_14_max,
        "fails": {
            "5d_60%": bool(cond1_fail),
            "15d_100%": bool(cond2_fail),
            "highest": bool(cond3_fail)
        }
    }
    
    return can_release, details

def get_release_schedule(df: pd.DataFrame, designation_date_str: str):
    """
    Calculates the release schedule starting from T+10 trading days.
    """
    try:
        designation_date = pd.to_datetime(designation_date_str)
        # Find the index of designation date in the dataframe
        # Some dataframes might have timezone info
        if df.index.tz is not None:
             designation_date = designation_date.tz_localize(df.index.tz)
             
        # Find exact or nearest next trading day
        designation_idxs = df.index.get_indexer([designation_date], method='nearest')
        start_idx = designation_idxs[0]
        
        # First determination day is T+10 trading days
        # T is designation date (idx start_idx)
        determination_start_idx = start_idx + 10
        
        if determination_start_idx >= len(df):
            return {
                "status": "waiting",
                "next_determination_date": None,
                "message": "최초 판단일(T+10)에 아직 도달하지 않았습니다."
            }
            
        results = []
        released_date = None
        
        # Check from determination_start_idx to today
        for i in range(determination_start_idx, len(df)):
            can_release, details = check_release_conditions(df, i)
            results.append(details)
            if can_release:
                released_date = df.index[i].strftime('%Y-%m-%d')
                break
        
        return {
            "status": "released" if released_date else "pending",
            "released_date": released_date,
            "determination_history": results,
            "next_thresholds": results[-1] if results else None
        }
        
    except Exception as e:
        return {"error": str(e)}
