import json, os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from earnings_provider import next_earnings_date

ROOT = Path(__file__).parent
BKK = ZoneInfo("Asia/Bangkok")
today = datetime.now(BKK).date()
tomorrow = today + timedelta(days=1)
watch = json.loads((ROOT / "config/watchlist.json").read_text())["tickers"]
sent_path = ROOT / "data/sent.json"
sent_path.parent.mkdir(exist_ok=True)
sent = json.loads(sent_path.read_text()) if sent_path.exists() else {"sent": []}
sent_set = set(sent.get("sent", []))
topic = os.environ.get("NTFY_TOPIC", "").strip()
ntfy_token = os.environ.get("NTFY_TOKEN", "").strip()
if not topic:
    raise SystemExit("Missing NTFY_TOPIC secret")

new_sent = []
for symbol in watch:
    try:
        earnings_date = next_earnings_date(symbol)
        if earnings_date != tomorrow:
            print(f"{symbol}: next earnings={earnings_date}; no alert today")
            continue
        key = f"{symbol}:{earnings_date.isoformat()}"
        if key in sent_set:
            print(f"{symbol}: already notified")
            continue
        title = f"Earnings tomorrow: {symbol}"
        message = (f"{symbol} มีกำหนดประกาศผลประกอบการวันพรุ่งนี้ "
                   f"({earnings_date.isoformat()})\n"
                   "เวลาออกงบอาจเปลี่ยนแปลงได้ โปรดตรวจสอบกับบริษัทอีกครั้ง")
        headers = {"Title": title, "Priority": "default", "Tags": "chart_with_upwards_trend"}
        if ntfy_token:
            headers["Authorization"] = f"Bearer {ntfy_token}"
        response = requests.post(f"https://ntfy.sh/{topic}", data=message.encode("utf-8"),
                                 headers=headers, timeout=20)
        response.raise_for_status()
        new_sent.append(key)
        print(f"{symbol}: notification sent")
    except Exception as exc:
        print(f"{symbol}: ERROR: {exc}")

if new_sent:
    sent["sent"] = sorted(sent_set.union(new_sent))
    sent["updated_at"] = datetime.now(BKK).isoformat()
    sent_path.write_text(json.dumps(sent, indent=2) + "\n", encoding="utf-8")
