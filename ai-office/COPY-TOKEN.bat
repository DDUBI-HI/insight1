@echo off
rem AI-OFFICE launcher (ASCII only)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\copy-token.ps1" %1
pause
