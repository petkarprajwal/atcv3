@echo off
REM Unified ATC Dashboard Launcher for Windows
REM Usage: start_dashboard.bat [type] [port]

setlocal

REM Default values
set DASHBOARD_TYPE=realtime
set PORT=

REM Parse command line arguments
if "%1" neq "" set DASHBOARD_TYPE=%1
if "%2" neq "" set PORT=%2

echo 🚀 ATC AI Dashboard Launcher
echo ================================
echo Dashboard Type: %DASHBOARD_TYPE%
if "%PORT%" neq "" echo Port: %PORT%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

REM Check if Streamlit is available
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ❌ Streamlit not found. Installing...
    pip install streamlit
    if errorlevel 1 (
        echo ❌ Failed to install Streamlit
        pause
        exit /b 1
    )
)

REM Build launch command
set LAUNCH_CMD=python launch.py --type %DASHBOARD_TYPE%
if "%PORT%" neq "" set LAUNCH_CMD=%LAUNCH_CMD% --port %PORT%

echo 🚀 Launching dashboard...
echo Command: %LAUNCH_CMD%
echo.

REM Launch the dashboard
%LAUNCH_CMD%

if errorlevel 1 (
    echo.
    echo ❌ Dashboard launch failed
    echo.
    echo 🔧 Troubleshooting Tips:
    echo 1. Check if port is available
    echo 2. Try: start_dashboard.bat %DASHBOARD_TYPE% 8502
    echo 3. Check firewall settings
    echo 4. Run: pip install -r requirements.txt
    echo.
    pause
)

endlocal