# Local Search Rank Tracker

**فارسی:** [راهنمای فارسی](README.fa.md) · **English:** [English guide](README.en.md)

A local Persian-first web app for tracking Google search-result positions for multiple projects and domains. It uses SQLite for local history and Playwright for user-triggered, limited checks.

## Quick start on Windows

1. Install Python 3.10 or newer.
2. Double-click [`run.bat`](run.bat).
3. On first run, allow the script to install the Python packages. It uses system Chrome/Edge if present; otherwise, it attempts to download Playwright Chromium. If no browser is available, the UI still starts and explains the rank-check requirement.
4. Add a project, a search query and a target domain, then click **بررسی رتبه**.

Setup requires internet access to install dependencies and the browser. Google searches also require internet access. CAPTCHA is not bypassed: a check stops if one is detected.

## Local data and privacy

Projects and check history are stored in `rank_tracker.sqlite3` beside the app. The app binds to `127.0.0.1` and has no cloud backend. The Persian UI and Vazirmatn font are served from local project files.

Results are best-effort observations of Google's changing page layout; they are not guaranteed SEO rankings. See the language-specific guides for details, limitations, and tests.
