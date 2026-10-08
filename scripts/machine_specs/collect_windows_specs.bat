@echo off
REM Double-click to refresh this machine's specs (writes windows_laptop_specs.raw.json next to this file).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0collect_windows_specs.ps1"
