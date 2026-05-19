@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "SETTINGS=%SCRIPT_DIR%..\settings.py"

rem --- Locate Python interpreter -------------------------------------
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    echo ERROR: Python 3 not found. Install from https://www.python.org/
    exit /b 1
)

%PY% "%SETTINGS%"
endlocal
