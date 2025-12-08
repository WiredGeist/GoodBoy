@echo off
TITLE Arc Raiders Bounty Hunter - GOOD BOY
CLS

echo ==================================================
echo      INSTALLING GOOD BOY...
echo ==================================================
echo.

IF NOT EXIST "venv" (
    python -m venv venv
)

venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m pip install "https://github.com/KittenML/KittenTTS/releases/download/0.1/kittentts-0.1.0-py3-none-any.whl"
venv\Scripts\python.exe -m playwright install chromium

CLS
echo ==================================================
echo           SYSTEM READY - STARTING...
echo ==================================================
venv\Scripts\python.exe main.py
pause