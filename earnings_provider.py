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


def previous_earnings_date(symbol: str, today: date | None = None):
    """Return the latest past earnings-report date Yahoo provides, if available.

    Yahoo's earnings-dates history can be incomplete for some tickers.
    None means no usable historical date was returned; it is not a statement
    that the company did not report earnings.
    """
    today = today or date.today()
    history = yf.Ticker(symbol).get_earnings_dates(limit=12)
    if history is None or getattr(history, "empty", True):
        return None

    reported_column = "Reported EPS" if "Reported EPS" in history.columns else None
    dates = []
    for index, row in history.iterrows():
        try:
            parsed = _as_date(index)
            if parsed is None or parsed > today:
                continue
            if reported_column and row[reported_column] is None:
                continue
            if reported_column:
                try:
                    import pandas as pd
                    if pd.isna(row[reported_column]):
                        continue
                except (ImportError, TypeError, ValueError):
                    pass
            dates.append(parsed)
        except (TypeError, ValueError, OverflowError):
            continue
    return max(dates) if dates else None
