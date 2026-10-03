@echo off
rem Antigravity Cross-Platform Execution Proxy for Windows CMD / PowerShell
python "%~dp0exec_proxy.py" %*
exit /b %ERRORLEVEL%
