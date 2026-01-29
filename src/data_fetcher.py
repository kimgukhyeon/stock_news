import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time

def get_stock_name(code: str) -> Optional[str]:
    """
    Fetches Korean stock name from various sources.
    Returns None if not found.
    """
    # Method 1: Try 네이버 증권 페이지 스크래핑
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 네이버 증권 페이지에서 종목명 추출
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text()
                # "삼성전자 : 네이버 증권" 형식에서 종목명 추출
                if ':' in title:
                    name = title.split(':')[0].strip()
                    if name and len(name) > 0:
                        return name
            # 또는 다른 선택자 시도
            wrap_company = soup.find('div', class_='wrap_company')
            if wrap_company:
                h2 = wrap_company.find('h2')
                if h2:
                    name = h2.get_text().strip()
                    if name:
                        return name
    except Exception:
        pass
    
    # Method 2: Try FinanceDataReader StockListing with retry
    for market in ['KRX', 'KRX-MARCAP']:
        try:
            df_krx = fdr.StockListing(market)
            if df_krx is not None and not df_krx.empty:
                match = df_krx[df_krx['Code'] == code]
                if not match.empty:
                    name = match.iloc[0].get('Name', None)
                    if name:
                        return name
            time.sleep(0.5)  # Rate limiting
        except Exception:
            continue
    
    # Method 3: Fallback to yfinance (English name)
    try:
        ticker = yf.Ticker(f"{code}.KS")
        info = ticker.info
        if info and 'longName' in info:
            return info['longName']
        if info and 'shortName' in info:
            return info['shortName']
    except Exception:
        pass
    
    return None

def get_stock_data(code, days=120):
    """
    Fetches OHLCV data for the given stock code.
    Fetches enough data to calculate moving averages (approx 120 days).
    """
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    
    # fdr uses 'code' which can be KRX stock code
    # e.g. '005930' for Samsung Electronics
    try:
        df = fdr.DataReader(code, start_date, end_date)
        return df
    except Exception as e:
        print(f"Error fetching data for {code}: {e}")
        return None
