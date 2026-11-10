@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 IndexCleaner.py
) else (
    python IndexCleaner.py
)
if errorlevel 1 (
    echo.
    echo Index Cleaner stopped with an error.
    pause
)
endlocal
