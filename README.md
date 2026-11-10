# Earnings Alert

<img width="779" height="882" alt="Screenshot 2026-11-10 102851" src="https://github.com/user-attachments/assets/5c989fe7-fd6a-41fe-a7d8-7351e2970e23" />

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
