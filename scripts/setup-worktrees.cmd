@echo off
rem Antigravity Cross-Platform setup_worktrees for Windows CMD / PowerShell
python "%~dp0setup_worktrees.py" %*
exit /b %ERRORLEVEL%
