@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ^>^> Claude Code Status Line - Windows Setup

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%..\.."
set "SRC=%REPO_ROOT%\scripts\statusline.py"
set "DEST_DIR=%USERPROFILE%\.claude"
set "DEST=%DEST_DIR%\statusline.py"

rem --- Locate a Python interpreter (python or py launcher) -----------
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
    echo        Bitte ein neues Terminal oeffnen und install.cmd erneut ausfuehren.
    exit /b 1
)

rem --- Install windows-curses for the configure.py TUI ----------------
%PY% -m pip install --quiet windows-curses
if errorlevel 1 (
    echo WARN: Could not install windows-curses. configure.py TUI may not work.
)

rem --- Locate git ----------------------------------------------------
where git >nul 2>nul || (
    echo ERROR: 'git' is required but not installed.
    echo See https://git-scm.com/download/win
    exit /b 1
)

rem --- Verify source -------------------------------------------------
if not exist "%SRC%" (
    echo ERROR: Source file not found: %SRC%
    exit /b 1
)

rem --- Copy statusline.py into ~/.claude/ -----------------------------
if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"
copy /Y "%SRC%" "%DEST%" >nul || (
    echo ERROR: Failed to copy %SRC% to %DEST%
    exit /b 1
)
echo    installed: %DEST%

rem --- Merge statusLine entry into settings.json ---------------------
%PY% "%SCRIPT_DIR%..\_settings.py" install
if errorlevel 1 (
    echo ERROR: Failed to update settings.json
    exit /b 1
)

rem --- Default-Config anlegen (nur bei Erstinstallation) ----------------
set "CONFIG_DEST=%USERPROFILE%\.claude\statusline_config.json"
set "CONFIG_SRC=%REPO_ROOT%\setup\default_config.json"
if not exist "%CONFIG_DEST%" if exist "%CONFIG_SRC%" (
    copy /Y "%CONFIG_SRC%" "%CONFIG_DEST%" >nul
    echo    installed: %CONFIG_DEST% (default config^)
)

echo ^>^> Done. Restart Claude Code to load the status line.
endlocal
