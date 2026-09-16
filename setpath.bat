@echo off
set "OLDPATH="
for /f "skip=2 tokens=2,*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "OLDPATH=%%b"
reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "%OLDPATH%;%LOCALAPPDATA%\1b1t" /f >nul
