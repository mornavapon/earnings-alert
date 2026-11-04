import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import quote

import requests
from earnings_provider import next_earnings_date, previous_earnings_date

def financial_url(symbol: str) -> str:
    """Build the same financial-statement destination used by the web app."""
    symbol = symbol.strip().upper()
    if symbol.endswith(".BK"):
        code = quote(symbol[:-3].lower(), safe="")
        return f"https://www.settrade.com/th/equities/quote/{code}/news"

    parts = symbol.rsplit(".", 1)
    if len(parts) == 2 and parts[1] in {"HK", "SS", "SZ"}:
        market = {"HK": "hkg", "SS": "sha", "SZ": "she"}[parts[1]]
        code = quote(parts[0], safe="")
        return f"https://stockanalysis.com/quote/{market}/{code}/financials/"

    return f"https://stockanalysis.com/stocks/{quote(symbol.lower(), safe='')}/financials/"


ROOT = Path(__file__).parent
BKK = ZoneInfo("Asia/Bangkok")
now = datetime.now(BKK)
today = now.date()
tomorrow = today + timedelta(days=1)
watch = json.loads((ROOT / "config/watchlist.json").read_text(encoding="utf-8"))["tickers"]
sent_path = ROOT / "data/sent.json"
snapshot_path = ROOT / "data/earnings.json"
sent_path.parent.mkdir(exist_ok=True)
sent = json.loads(sent_path.read_text(encoding="utf-8")) if sent_path.exists() else {"sent": []}
sent_set = set(sent.get("sent", []))
topic = os.environ.get("NTFY_TOPIC", "").strip()
ntfy_token = os.environ.get("NTFY_TOKEN", "").strip()
if not topic:
    raise SystemExit("Missing NTFY_TOPIC secret")

snapshot = {
    "updated_at": now.isoformat(),
    "source": "Yahoo Finance via yfinance",
    "tickers": {}
}
new_sent = []

for symbol in watch:
    item = {}
    try:
        previous_date = previous_earnings_date(symbol, today=today)
        if previous_date:
            item["previous_date"] = previous_date.isoformat()
            print(f"{symbol}: previous earnings={previous_date.isoformat()}")
        else:
            print(f"{symbol}: Yahoo returned no previous earnings date")
    except Exception as exc:
        print(f"{symbol}: previous earnings lookup unavailable: {exc}")

    try:
        earnings_date = next_earnings_date(symbol, today=today)
        if earnings_date is None:
            item.update({
                "status": "no_date",
                "message": "Yahoo ยังไม่แสดงกำหนดวันประกาศงบ"
            })
            snapshot["tickers"][symbol] = item
            print(f"{symbol}: Yahoo returned no upcoming earnings date")
            continue

        iso_date = earnings_date.isoformat()
        item.update({
            "status": "scheduled",
            "date": iso_date,
            "message": f"จะประกาศงบวันที่ {iso_date}"
        })
        snapshot["tickers"][symbol] = item
        print(f"{symbol}: next earnings={iso_date}")

        if earnings_date != tomorrow:
            continue

        key = f"{symbol}:{iso_date}"
        if key in sent_set:
            print(f"{symbol}: already notified")
            continue

        title = f"Earnings tomorrow: {symbol}"
        report_url = financial_url(symbol)
        message = (f"{symbol} มีกำหนดประกาศผลประกอบการวันพรุ่งนี้ "
                   f"({iso_date})\n"
                   "แตะการแจ้งเตือนเพื่อเปิดดูงบการเงินล่าสุด\n"
                   f"{report_url}\n"
                   "เวลาออกงบอาจเปลี่ยนแปลงได้ โปรดตรวจสอบกับบริษัทอีกครั้ง")
        headers = {
            "Title": title,
            "Priority": "default",
            "Tags": "chart_with_upwards_trend",
            "Click": report_url,
        }
        if ntfy_token:
            headers["Authorization"] = f"Bearer {ntfy_token}"
        response = requests.post(
            f"https://ntfy.sh/{topic}", data=message.encode("utf-8"),
            headers=headers, timeout=20
        )
        response.raise_for_status()
        new_sent.append(key)
        print(f"{symbol}: notification sent")
    except Exception as exc:
        item.update({
            "status": "error",
            "message": "ดึงข้อมูลไม่สำเร็จ กรุณาลองใหม่"
        })
        snapshot["tickers"][symbol] = item
        print(f"{symbol}: ERROR: {exc}")

snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if new_sent:
    sent["sent"] = sorted(sent_set.union(new_sent))
    sent["updated_at"] = now.isoformat()
    sent_path.write_text(json.dumps(sent, indent=2) + "\n", encoding="utf-8")
