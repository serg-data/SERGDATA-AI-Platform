@echo off
setlocal
cd /d "%~dp0" || goto :startup_error

rem Use UTF-8 for Russian diagnostics and Python output.
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

where powershell.exe >nul 2>&1
if errorlevel 1 goto :powershell_missing

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
set "WORKBENCH_EXIT=%ERRORLEVEL%"
if not "%WORKBENCH_EXIT%"=="0" (
    echo.
    echo SERGDATA Workbench failed with exit code %WORKBENCH_EXIT%.
    pause
)
exit /b %WORKBENCH_EXIT%

:powershell_missing
echo Windows PowerShell was not found. Install or enable Windows PowerShell.
goto :startup_error

:startup_error
echo.
echo Unable to start SERGDATA Workbench.
pause
exit /b 1
