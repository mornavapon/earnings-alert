# Earnings Alert

<img width="639" height="743" alt="Screenshot 2026-11-10 103132" src="https://github.com/user-attachments/assets/1c99eb96-4f00-4223-b02a-c9a2b1ca6260" />

ลิ้งค์ไปยังเอไอที่สร้างแอป
https://chatgpt.com/g/g-p-6ae01a981d208191b90116a6a767d75e-github/c/6af13eb7-5598-83ec-84ee-bf218f4d985a

A free GitHub Pages + GitHub Actions app for a personal US-stock earnings watchlist. Yahoo Finance data is accessed through `yfinance`; notifications are sent to ntfy.

## Important limitations
- Yahoo Finance does not provide a stable, documented free earnings-calendar API for this workflow. `yfinance` relies on Yahoo endpoints and may stop working or be rate-limited.
- Earnings dates can be estimates and may change. This MVP alerts based on the next date returned by Yahoo; verify important dates with the company.
- The app's Watchlist editor uses a fine-grained GitHub token in this browser. Restrict it to this repository only, grant Contents read/write, set an expiration, and revoke it if the device/browser is shared or compromised.
- No EPS/revenue results are collected; this app only reminds you before the event.

## 1. GitHub Pages
Repository Settings → Pages → Deploy from a branch → `main` → `/ (root)` → Save.

## 2. GitHub token for Watchlist editing
GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token.
- Resource owner: `mornavapon`
- Repository access: Only select repositories → `earnings-alert`
- Repository permissions: Contents = Read and write
- Set an expiration date.
Paste the token into the app's GitHub Token field and press Connect. Do not share the token.

## 3. ntfy secrets
Repository Settings → Secrets and variables → Actions → New repository secret:
- `NTFY_TOPIC`: your private ntfy topic name (same topic configured on Android)
- `NTFY_TOKEN`: optional; leave unset if your topic is public/unprotected.

## 4. Workflow
Actions → Earnings Alert → Run workflow to test. Scheduled run is daily at 02:00 UTC (09:00 Thailand time). GitHub scheduled workflows can be delayed during busy periods.

## Files
- `index.html`, `style.css`, `app.js`: GitHub Pages frontend
- `config/watchlist.json`: source of truth for tracked symbols
- `earnings_provider.py`: Yahoo data adapter; replace this module to change provider
- `check_earnings.py`: daily alert logic
- `.github/workflows/earnings-alert.yml`: scheduled workflow
- `data/sent.json`: duplicate-notification history
