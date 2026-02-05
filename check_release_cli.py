import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from data_fetcher import get_stock_data, get_stock_name
from checkers.warning_release import get_release_schedule

def main():
    if len(sys.argv) < 3:
        print("Usage: python check_release_cli.py <stock_code> <designation_date>")
        print("Example: python check_release_cli.py 032820 2026-01-22")
        return

    code = sys.argv[1]
    designation_date = sys.argv[2]
    
    name = get_stock_name(code)
    print(f"--- [{name or code}] 투자경고 해제 분석 ---")
    print(f"지정일: {designation_date}")
    
    # Fetch 120 days of data to ensure we have T-15
    df = get_stock_data(code, days=120)
    
    if df is None or df.empty:
        print("데이터를 가져오는데 실패했습니다.")
        return
        
    schedule = get_release_schedule(df, designation_date)
    
    if "error" in schedule:
        print(f"오류 발생: {schedule['error']}")
        return
        
    if schedule['status'] == "released":
        print(f"✅ 해제 완료: {schedule['released_date']}")
    else:
        print(f"⏳ 해제 대기 중 (상태: {schedule['status']})")
        
    if schedule.get('determination_history'):
        print("\n[최근 판단 내역]")
        for item in schedule['determination_history'][-3:]: # Show last 3
            status = "통과" if not any(item['fails'].values()) else "불가"
            print(f"- {item['date']}: {item['close']:,.0f}원 (기준: {item['release_ceiling']:,.0f}원 미만) -> {status}")
            if status == "불가":
                fails = [k for k, v in item['fails'].items() if v]
                print(f"  * 위반 요건: {', '.join(fails)}")

    if schedule['status'] == "pending" and schedule.get('determination_history'):
        last = schedule['determination_history'][-1]
        print(f"\n💡 다음 판단일 해제 요건 (현재가 기준):")
        print(f"  - 종가가 {last['release_ceiling']:,.0f}원 미만이어야 합니다.")
        print(f"  (참고: 5일전 160%={last['thresh_5d']:,.0f}, 15일전 200%={last['thresh_15d']:,.0f}, 15일간 최고가={last['prev_14_max']:,.0f})")

if __name__ == "__main__":
    main()
