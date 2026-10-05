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

"%PYTHON%" -c "from importlib.metadata import version; assert version('playwright') == '1.60.0' and version('streamlit') == '1.65.0'" >nul 2>&1
if errorlevel 1 (
    "%PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 goto setup_failed
)

if not exist "browser-runtime\.chromium-installed" (
    if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" goto launch_app
    if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" goto launch_app
    if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" goto launch_app
    if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" goto launch_app
    if exist "%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe" goto launch_app
    "%PYTHON%" -m playwright install chromium
    if errorlevel 1 goto browser_install_warning
    >"browser-runtime\.chromium-installed" echo installed
)

:launch_app
"%PYTHON%" -m streamlit run app.py --server.address 127.0.0.1
goto finished

:python_missing
echo Python 3.10 or newer is required. Install it from https://www.python.org/downloads/ and run this file again.
goto failed

:browser_install_warning
echo Chromium could not be downloaded. The app will still start.
echo Rank checks can use an installed Chrome or Edge; otherwise reconnect and run this file again.
goto launch_app

:setup_failed
echo Project setup failed. Check the error above and run this file again.
goto failed

:failed
pause
exit /b 1

:finished
exit /b %errorlevel%
