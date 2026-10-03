@echo off
rem Antigravity Cross-Platform Release Gate for Windows CMD / PowerShell
python "%~dp0verify_release_gate.py" %*
exit /b %ERRORLEVEL%
