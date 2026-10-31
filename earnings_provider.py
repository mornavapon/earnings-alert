"""Yahoo Finance provider adapter. Replace this module to change data source later."""
from datetime import date
import yfinance as yf

def next_earnings_date(symbol: str):
    """Return the next earnings date as a date, or None if Yahoo has no date."""
    ticker = yf.Ticker(symbol)
    cal = ticker.calendar
    if cal is None:
        return None
    values = None
    if isinstance(cal, dict):
        values = cal.get("Earnings Date")
    else:
        try:
            values = cal.loc["Earnings Date"].tolist()
        except Exception:
            return None
    if values is None:
        return None
    if not isinstance(values, (list, tuple)):
        values = [values]
    dates = []
    for value in values:
        try:
            d = value.date() if hasattr(value, "date") else date.fromisoformat(str(value)[:10])
            if d >= date.today():
                dates.append(d)
        except Exception:
            continue
    return min(dates) if dates else None
