from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from src.data_fetcher import get_stock_data, get_stock_name
from src.indicators import calculate_indicators
from src.checkers.overheating import check_overheating
from src.checkers.caution import check_caution
from src.checkers.warning import check_warning


def _to_builtin(v: Any) -> Any:
    """
    Convert pandas/numpy-ish scalars into JSON-serializable builtin types.
    """
    # pandas.Timestamp / datetime-like
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.strftime("%Y-%m-%d")

    # pandas / numpy scalars
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass

    # dict / list recursion
    if isinstance(v, dict):
        return {str(k): _to_builtin(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_to_builtin(x) for x in v]

    return v


def generate_stock_report(code: str, date: Optional[str] = None) -> dict[str, Any]:
    """
    Generate a JSON-friendly report for a KRX stock code.

    - code: e.g. "005930"
    - date: 기준일(YYYY-MM-DD). 주어지면 해당 날짜 이하 데이터만 사용
    """
    code = str(code).strip()
    if not code:
        return {"ok": False, "error": {"message": "종목코드를 입력해주세요."}}

    # Get stock name
    stock_name = get_stock_name(code)

    df = get_stock_data(code)
    if df is None or df.empty:
        return {"ok": False, "error": {"message": "데이터 조회 실패. 종목코드를 확인해주세요."}}

    if date:
        try:
            # Accept YYYY-MM-DD; allow datetime-like strings that pandas can parse.
            cutoff = pd.to_datetime(date).date()
        except Exception:
            return {"ok": False, "error": {"message": "date 형식이 올바르지 않습니다. (YYYY-MM-DD)"}}

        df = df[df.index.date <= cutoff]
        if df.empty:
            return {
                "ok": False,
                "error": {"message": f"해당 날짜({date}) 이전 데이터가 없습니다."},
            }

    df = calculate_indicators(df)

    oh_triggered, oh_details = check_overheating(df)
    ca_triggered, ca_details = check_caution(df)
    wa_triggered, wa_details = check_warning(df)

    latest = df.iloc[-1]
    latest_date = df.index[-1]

    report = {
        "ok": True,
        "input": {"code": code, "date": date},
        "meta": {
            "as_of": _to_builtin(latest_date),
            "latest_close": _to_builtin(latest.get("Close")),
            "currency": "KRW",
            "stock_name": stock_name,  # 종목명
        },
        "status": {
            "caution": bool(ca_triggered),  # 투자주의종목
            "warning": bool(wa_triggered),  # 투자경고종목
            "margin": None,  # 증거금종목 여부 (추후 구현)
            "credit": None,  # 신용가능 여부 (추후 구현)
        },
        "results": {
            "overheating": {
                "triggered": bool(oh_triggered),
                "details": _to_builtin(oh_details),
            },
            "caution": {
                "triggered": bool(ca_triggered),
                "details": _to_builtin(ca_details),
            },
            "warning": {
                "triggered": bool(wa_triggered),
                "details": _to_builtin(wa_details),
            },
        },
    }

    return report

