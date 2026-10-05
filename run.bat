@echo off
setlocal
cd /d "%~dp0"

set "PY_LAUNCHER=py -3"
where py >nul 2>&1
if errorlevel 1 set "PY_LAUNCHER=python"

%PY_LAUNCHER% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto python_missing

if not exist ".venv\Scripts\python.exe" (
    %PY_LAUNCHER% -m venv .venv
    if errorlevel 1 goto setup_failed
)

set "PYTHON=%CD%\.venv\Scripts\python.exe"
set "PLAYWRIGHT_BROWSERS_PATH=%CD%\browser-runtime"
set "RANK_TRACKER_DB=%CD%\rank_tracker.sqlite3"

"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto setup_failed

if not exist "browser-runtime\.chromium-installed" (
    "%PYTHON%" -m playwright install chromium
    if errorlevel 1 goto browser_failed
    >"browser-runtime\.chromium-installed" echo installed
)

"%PYTHON%" -m streamlit run app.py --server.address 127.0.0.1
goto finished

:python_missing
echo Python 3.10 or newer is required. Install it from https://www.python.org/downloads/ and run this file again.
goto failed

:browser_failed
echo Chromium could not be downloaded. Check your internet connection and run this file again.
goto failed

:setup_failed
echo Project setup failed. Check the error above and run this file again.
goto failed

:failed
pause
exit /b 1

:finished
exit /b %errorlevel%
