@echo off
REM Double-click to download/resume the pinned PanTS archives onto the QUINN external drive.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0download_pants_windows.ps1"
echo.
echo Finished (exit code %ERRORLEVEL%). This window can be closed.
pause
