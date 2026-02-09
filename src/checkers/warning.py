def check_warning(df):
    """
    Checks for Investment Warning criteria (지정예고 요건 중심).

    참고: KRX '투자경고종목 지정예고요건' 및 주의사항
    - https://moc.krx.co.kr/contents/SVL/M/03020100/MOC03020100.jsp

    중요:
    - 공식 요건에는 시장지수 대비 상승률, 계좌(군) 관여율 등 추가 데이터가 필요합니다.
      본 프로젝트는 OHLCV만 있으므로 '가격 요건'만 근사해서 판단합니다.
    - '해당일의 종가가 최근 15일 종가 중 최고가' 조건을 적용합니다.

    구현(OHLCV 기반):
    - 초단기 급등: 3일 전 종가 대비 +100% 이상
    - 단기 급등: 5일 전 종가 대비 +60% 이상
    - 중장기 급등: 15일 전 종가 대비 +100% 이상
    - 중장기 급등: 15일 전 종가 대비 +100% 이상

    Returns: (is_triggered, details)
    """
    if df is None or len(df) < 15:
        return False, "데이터 부족"
        
    latest = df.iloc[-1]
    
    change_3d = float(latest.get("Change_3d", 0) or 0)
    change_5d = float(latest.get("Change_5d", 0) or 0)
    change_15d = float(latest.get("Change_15d", 0) or 0)
    
    # Base prices for calculation
    price_3d_ago = df.iloc[-4]['Close'] if len(df) >= 4 else None
    price_5d_ago = df.iloc[-6]['Close'] if len(df) >= 6 else None
    price_15d_ago = df.iloc[-16]['Close'] if len(df) >= 16 else None

    # "해당일 종가가 최근 15일 종가 중 최고가" (공식 주의사항)
    recent_15 = df.iloc[-15:]["Close"]
    max_close_15 = float(recent_15.max())
    current_close = float(latest["Close"])
    is_highest_close_15d = current_close >= max_close_15

    caution_days = 0
    # Investment caution repeat logic removed per user request

    # Thresholds (지정예고요건)
    thresh_3d = 1.00   # 초단기 급등
    thresh_5d = 0.60   # 단기 급등
    thresh_15d = 1.00  # 중장기 급등

    cond_3d = is_highest_close_15d and (change_3d >= thresh_3d)
    cond_5d = is_highest_close_15d and (change_5d >= thresh_5d)
    cond_15d = is_highest_close_15d and (change_15d >= thresh_15d)

    target_price_3d = price_3d_ago * (1 + thresh_3d) if price_3d_ago is not None else None
    target_price_5d = price_5d_ago * (1 + thresh_5d) if price_5d_ago is not None else None
    target_price_15d = price_15d_ago * (1 + thresh_15d) if price_15d_ago is not None else None

    is_triggered = cond_3d or cond_5d or cond_15d

    # Description 생성: 조건 충족 여부에 따라 동적으로 표시
    desc_3d_base = "당일 종가가 3일 전날 종가 대비 100% 이상 상승"
    desc_5d_base = "당일 종가가 5일 전날 종가 대비 60% 이상 상승"
    desc_15d_base = "당일 종가가 15일 전날 종가 대비 100% 이상 상승"
    
    # KRX 공식: "해당일의 종가가 최근 15일 종가 중 최고가인 경우에 한함"
    # 따라서 모든 조건에 최근 15일 최고가 조건이 필요하지만,
    # description에는 실제로 해당 조건이 충족되었을 때만 표시
    desc_3d = desc_3d_base + (" (최근 15일 종가 최고가)" if is_highest_close_15d else "")
    desc_5d = desc_5d_base + (" (최근 15일 종가 최고가)" if is_highest_close_15d else "")
    desc_15d = desc_15d_base + (" (최근 15일 종가 최고가)" if is_highest_close_15d else "")

    details = {
        "초단기급등(3일)": {
            "val": change_3d,
            "threshold": thresh_3d,
            "triggered": bool(cond_3d),
            "target_price": target_price_3d,
            "at_max": is_highest_close_15d,
            "description": desc_3d,
        },
        "단기급등(5일)": {
            "val": change_5d,
            "threshold": thresh_5d,
            "triggered": bool(cond_5d),
            "target_price": target_price_5d,
            "at_max": is_highest_close_15d,
            "description": desc_5d,
        },
        "중장기급등(15일)": {
            "val": change_15d,
            "threshold": thresh_15d,
            "triggered": bool(cond_15d),
            "target_price": target_price_15d,
            "at_max": is_highest_close_15d,
            "description": desc_15d,
        }
    }

    return is_triggered, details
