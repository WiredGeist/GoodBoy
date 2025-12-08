@echo off
TITLE Arc Raiders Bounty Hunter - GOOD BOY
CLS

echo ==================================================
echo      INITIALIZING FREQUENCIES...
echo ==================================================
echo.

:: 1. Create Virtual Environment if missing
IF NOT EXIST "venv" (
    echo [INFO] Creating new virtual environment...
    python -m venv venv
)

:: 2. Upgrade PIP
echo [INFO] Upgrading installer...
venv\Scripts\python.exe -m pip install --upgrade pip

:: 3. Force Install Gradio and Essentials (Directly)
echo [INFO] Installing Core AI Modules...
venv\Scripts\python.exe -m pip install gradio opencv-python mss numpy sounddevice scipy pandas python-dotenv playwright google-genai rapidocr-onnxruntime

:: 4. Install Custom TTS
echo [INFO] Installing Voice Module...
venv\Scripts\python.exe -m pip install "https://github.com/KittenML/KittenTTS/releases/download/0.1/kittentts-0.1.0-py3-none-any.whl"

:: 5. Install Browsers
echo [INFO] Installing Browser Engine...
venv\Scripts\python.exe -m playwright install chromium

CLS
echo ==================================================
echo           SYSTEM READY - STARTING...
echo ==================================================
venv\Scripts\python.exe main.py
pause
