"""Yahoo Finance provider adapter. Replace this module to change data source later."""
from datetime import date, datetime
import yfinance as yf


def _as_date(value):
    if value is None:
        return None
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def next_earnings_date(symbol: str, today: date | None = None):
    """Return the next date Yahoo supplies, or None when Yahoo supplies no date.

    None means 'no date currently supplied by Yahoo'; it does NOT prove that
    the company has not announced an earnings date.
    """
    today = today or date.today()
    calendar = yf.Ticker(symbol).calendar
    if calendar is None:
        return None

    values = None
    if isinstance(calendar, dict):
        values = calendar.get("Earnings Date")
    else:
        try:
            values = calendar.loc["Earnings Date"]
            if hasattr(values, "tolist"):
                values = values.tolist()
        except (KeyError, AttributeError, TypeError):
            return None

    if values is None:
        return None
    if not isinstance(values, (list, tuple)):
        values = [values]

    dates = []
    for value in values:
        try:
            parsed = _as_date(value)
            if parsed and parsed >= today:
                dates.append(parsed)
        except (TypeError, ValueError, OverflowError):
            continue
    return min(dates) if dates else None
