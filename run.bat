@echo off
chcp 65001 >nul
title Samane Modiriat Daneshgahi - University Management System

REM ===== اجرای برنامه در ویندوز =====
REM اگر Python نصب نیست: https://www.python.org/downloads/ و تیک "Add python.exe to PATH" را بزنید

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python found nashod!_lotfan Python ra nasb konid.
  pause
  exit /b 1
)

if not exist ".venv" (
  echo [1/3] Sakht mahit majazi (.venv)...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip
  echo [2/3] Nasb ketabkhaneha...
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)

echo [3/3] Ejra barname...
echo.
echo   Address: http://127.0.0.1:5000
echo   Username: admin   Password: admin123
echo.
python app.py
pause
