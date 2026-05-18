@echo off
setlocal EnableExtensions

echo ^>^> Claude Code Status Line - Windows Uninstall

set "SCRIPT_DIR=%~dp0"
set "DEST=%USERPROFILE%\.claude\statusline.py"

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    echo ERROR: Python 3 is required but was not found in PATH.
    exit /b 1
)

if exist "%DEST%" (
    del /Q "%DEST%" && echo    removed: %DEST%
) else (
    echo    skipped: %DEST% ^(not found^)
)

%PY% "%SCRIPT_DIR%_settings.py" uninstall

echo ^>^> Done. Restart Claude Code.
endlocal
