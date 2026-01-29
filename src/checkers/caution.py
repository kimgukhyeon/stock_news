def check_caution(df):
    """
    Checks for Investment Caution criteria.
    참고: KRX 투자주의종목 기준 (https://moc.krx.co.kr/contents/SVL/M/03010100/MOC03010100.jsp)
    
    OHLCV 데이터만 사용 가능한 조건:
    1. 소수계좌거래집중종목: 최근 3일간 주가상승률 15% 이상 (시장지수 8% 이상일 경우 25% 이상)
    2. 종가급변종목: 종가가 직전가격 대비 5% 이상 상승(하락) + 거래량 3만주 이상
    3. 15일간 상승종목: 최근 15일간 주가상승률 75% 이상
    4. 특정계좌(군) 매매관여 과다: 최근 3일간 주가상승률 15% 이상 (시장지수 8% 이상일 경우 25% 이상)
    
    Returns: (is_triggered, details)
    """
    if df is None or len(df) < 15:
        return False, "데이터 부족"
        
    latest = df.iloc[-1]
    
    # 가격 변동률
    change_1d = latest.get('Change_1d', 0)  # 전일 대비
    change_3d = latest.get('Change_3d', 0)
    change_15d = latest.get('Change_15d', 0)
    change_from_prev = latest.get('Change_from_prev', 0)  # 직전가격 대비
    
    # 거래량 정보
    current_volume = latest.get('Volume', 0)
    
    # 최근 3일 평균 거래량
    recent_3d_vol = df.iloc[-3:]['Volume'].mean() if len(df) >= 3 else current_volume
    
    # Base prices for calculation
    price_3d_ago = df.iloc[-4]['Close'] if len(df) >= 4 else None
    price_15d_ago = df.iloc[-16]['Close'] if len(df) >= 16 else None
    prev_close = df.iloc[-2]['Close'] if len(df) >= 2 else None
    
    # KRX 투자주의종목 기준 (OHLCV 데이터 기반)
    # 1. 소수계좌거래집중종목: 최근 3일간 주가상승률 15% 이상
    #    (시장지수 8% 이상일 경우 25% 이상 - 시장지수 정보 없으므로 15% 기준)
    thresh_3d_caution_normal = 0.15
    thresh_3d_caution_high = 0.25  # 시장지수 상승률 높을 때
    thresh_3d_volume = 30000  # 일평균거래량 3만주 이상
    
    # 2. 종가급변종목: 종가가 직전가격 대비 5% 이상 상승(하락)
    #    + 종가 거래량이 전체 거래량의 5% 이상 (정확한 종가 거래량 없으므로 전체 거래량 사용)
    #    + 전체 거래량 3만주 이상
    thresh_close_change = 0.05
    thresh_close_vol_ratio = 0.05
    thresh_total_volume = 30000
    
    # 3. 15일간 상승종목: 최근 15일간 주가상승률 75% 이상
    thresh_15d_caution = 0.75
    
    # 조건 체크
    # 1. 소수계좌거래집중종목 (3일 15% 이상 + 거래량 3만주 이상)
    cond_3d_rise = change_3d >= thresh_3d_caution_normal
    cond_3d_volume = recent_3d_vol >= thresh_3d_volume
    cond_minority_account = cond_3d_rise and cond_3d_volume
    
    # 2. 종가급변종목 (직전가격 대비 5% 이상 + 거래량 3만주 이상)
    # 주의: 종가 거래량 비율은 정확히 계산 불가하므로, 전체 거래량만 체크
    cond_close_change = abs(change_from_prev) >= thresh_close_change
    cond_close_volume = current_volume >= thresh_total_volume
    cond_close_abrupt = cond_close_change and cond_close_volume
    
    # 3. 15일간 상승종목 (15일 75% 이상)
    cond_15d_rise = change_15d >= thresh_15d_caution
    
    # 4. 특정계좌(군) 매매관여 과다 (3일 15% 이상 + 거래량 3만주 이상)
    cond_specific_account = cond_3d_rise and cond_3d_volume
    
    target_price_3d = price_3d_ago * (1 + thresh_3d_caution_normal) if price_3d_ago is not None else None
    target_price_15d = price_15d_ago * (1 + thresh_15d_caution) if price_15d_ago is not None else None
    
    # 투자주의종목: 위 조건 중 하나라도 충족
    is_triggered = cond_minority_account or cond_close_abrupt or cond_15d_rise or cond_specific_account
    
    details = {
        "소수계좌거래집중(3일)": {
            "val": change_3d,
            "threshold": thresh_3d_caution_normal,
            "triggered": bool(cond_minority_account),
            "target_price": target_price_3d,
            "volume": recent_3d_vol,
            "volume_threshold": thresh_3d_volume,
            "description": "최근 3일간 주가상승률 15% 이상 + 일평균거래량 3만주 이상"
        },
        "종가급변종목": {
            "val": change_from_prev,
            "threshold": thresh_close_change,
            "triggered": bool(cond_close_abrupt),
            "target_price": prev_close * (1 + thresh_close_change) if prev_close is not None else None,
            "volume": current_volume,
            "volume_threshold": thresh_total_volume,
            "description": "종가가 직전가격 대비 5% 이상 상승(하락) + 거래량 3만주 이상"
        },
        "15일간상승종목": {
            "val": change_15d,
            "threshold": thresh_15d_caution,
            "triggered": bool(cond_15d_rise),
            "target_price": target_price_15d,
            "description": "최근 15일간 주가상승률 75% 이상"
        },
        "특정계좌(군)매매관여과다": {
            "val": change_3d,
            "threshold": thresh_3d_caution_normal,
            "triggered": bool(cond_specific_account),
            "target_price": target_price_3d,
            "volume": recent_3d_vol,
            "volume_threshold": thresh_3d_volume,
            "description": "최근 3일간 주가상승률 15% 이상 + 일평균거래량 3만주 이상"
        }
    }
    
    return is_triggered, details
