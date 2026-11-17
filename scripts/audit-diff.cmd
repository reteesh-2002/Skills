@echo off
rem Antigravity Cross-Platform audit_diff for Windows CMD / PowerShell
python "%~dp0audit_diff.py" %*
exit /b %ERRORLEVEL%
