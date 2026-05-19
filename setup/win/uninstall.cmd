@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ^>^> Claude Code Status Line - Windows Uninstall

set "SCRIPT_DIR=%~dp0"
set "DEST=%USERPROFILE%\.claude\statusline.py"

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    echo.
    echo    Python 3 wurde nicht gefunden.
    set /p "INSTALL_PY=   Jetzt Python 3.12 via winget installieren? [J/N]: "
    if /i "!INSTALL_PY!"=="J" (
        echo    Installiere Python 3.12 via winget...
        winget install -e --id Python.Python.3.12
        if errorlevel 1 (
            echo ERROR: winget-Installation fehlgeschlagen.
            exit /b 1
        )
        where python >nul 2>nul && set "PY=python"
        if not defined PY set "PY=py -3"
    ) else (
        echo ERROR: Python 3 wird benoetigt. Setup abgebrochen.
        exit /b 1
    )
)
if not defined PY (
    echo ERROR: Python 3 nach Installation nicht gefunden.
    echo        Bitte ein neues Terminal oeffnen und uninstall.cmd erneut ausfuehren.
    exit /b 1
)

if exist "%DEST%" (
    del /Q "%DEST%" && echo    removed: %DEST%
) else (
    echo    skipped: %DEST% ^(not found^)
)

%PY% "%SCRIPT_DIR%..\_install_helper.py" uninstall

echo ^>^> Done. Restart Claude Code.
endlocal
