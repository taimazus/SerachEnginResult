<div lang="en" dir="ltr" align="left">

# Local Search Rank Tracker

[فارسی](README.fa.md)

A local web app for organizing projects, search queries, target domains, and rank-check history in SQLite. Searches are initiated only by an explicit user click.

## Persian UI, font, and dependencies

- The Persian UI is right-to-left and loads Vazirmatn from the local `static/Vazirmatn.woff2`; it does not require a font CDN or remote font service.
- The font license is included at `static/OFL.txt`.
- On Windows, `run.bat` prepares a project-local `.venv` and installs Python packages beside the project. Playwright uses installed Chrome or Edge when available; otherwise the script attempts to download a local Chromium. If no browser can be obtained, the UI still starts, but rank checks remain unavailable until a browser is installed.
- Python 3.10 or newer must already be installed. If it is missing, the batch file displays setup guidance but does not install Python itself.
- Downloaded Chromium is stored under `browser-runtime` and Python packages under `.venv`; these large local folders are excluded from Git. An existing system Chrome or Edge can be used instead.

## Scope and limitations

- Manual Google result checks with Playwright; up to 5 pages per run (3 by default).
- Requests use `gl=ir` and the browser locale `fa-IR`; these do not guarantee a user's exact location or actual ranking.
- If Google presents a CAPTCHA, the run stops and the event is recorded. The app does not bypass CAPTCHA, rotate proxies, schedule automatic runs, or disguise automation.
- Google's HTML and selectors may change. Treat results as observed estimates, not guaranteed or authoritative SEO data.
- Data is stored in `rank_tracker.sqlite3` beside the app. Set `RANK_TRACKER_DB` to use another path.
- There is no API or cloud service. Do not expose the app on a public network.

## Setup on Windows

```powershell
.\run.bat
```

On first run, the batch file downloads the Python packages. If Chrome or Edge is installed, no separate browser download is needed; otherwise it attempts to download Chromium. Keep it open until the local page starts, usually at `http://localhost:8501`. If no browser can be obtained, the UI still opens and a rank check reports how to proceed.

If an older app version is still open in the browser, close its previous run window, start `run.bat` again, and refresh the page so the updated code is loaded. Failed earlier runs remain in history but are shown as concise messages.

For manual setup:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\browser-runtime"
python -m playwright install chromium
streamlit run app.py --server.address 127.0.0.1
```

## Usage

1. Create a project.
2. Add a search query and target domain.
3. Click **Check rank** for that query.
4. Review the result and up to five recent runs.

Rank counts unique URLs extractable from organic results. Ads and `google.com` links are excluded. Google's layout and result count can differ from page-number assumptions.

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover SQLite persistence, validation, and domain matching. They do not send live requests to Google.

</div>
