🐕 Good Boy: An OCR & TTS Companion for ARC Raiders
Created by WiredGeist

### What is this?

"Good Boy" is a Python script I built as a fun coding challenge. It uses Optical Character Recognition (OCR) to read text from your screen (like a game's UI) and uses Text-to-Speech (TTS) to provide audio feedback.

Think of it as a glorified screen-reader that I over-engineered to see how well different Python libraries could work together in a real-time gaming environment. It’s a proof-of-concept, not a competitive tool.

> It reads pixels, sends requests, and talks back. That's it.

---

### ⚙️ Features (The Technical Bits)

*   **Real-Time Text Recognition:** Uses `RapidOCR` and `MSS` to capture and read text from user-defined screen regions, such as in-game chat UI.
*   **Dynamic Region Monitoring:** Can watch multiple screen areas simultaneously, including dynamic pop-ups like "KNOCKED OUT BY" notifications.
*   **API Integration:** Cross-references the recognized text with an external data source (currently configured for the Speranza community site via Playwright).
*   **AI Summarization & TTS:** Uses Google Gemini to process text and provides a brief audio summary via `KittenTTS`.
*   **Request Queue System:** Features a simple queue to manage multiple text detections in rapid succession, ensuring stable performance.
*   **Local Session History:** Saves a log of recognized names to a local file, with a simple Gradio dashboard for adding personal notes.

---

### 🛠️ The Tech Stack

*   **Interface:** `Gradio` (with a custom theme)
*   **Screen Capture:** `MSS`
*   **Optical Character Recognition:** `RapidOCR` & `OpenCV`
*   **Web Automation:** `Playwright` (for interacting with the data source)
*   **AI Model:** Google `Gemini Flash`
*   **Text-to-Speech:** `KittenTTS`

---

### 🚀 Getting Started

**1. Clone the repo**
```bash
git clone https://github.com/WiredGeist/GoodBoy.git
cd GoodBoy
```

**2. Add your API Key**
This is the only manual step. Before running anything, create a file named `.env` in the `GoodBoy` folder and add your Google Gemini API key like this:
```ini
GEMINI_API_KEY=your_key_goes_here
```

**3. Installation & Launch**

#### For Windows Users (Easy Method)
Simply double-click and run the `start_bounty_hunter.bat` file.

This script will automatically:
1.  Install all the required Python packages from `requirements.txt`.
2.  Set up the necessary browser component via `playwright`.
3.  Launch the main program (`main.py`).

#### For macOS/Linux or Manual Installation
If you aren't on Windows or prefer to install manually, run these commands in your terminal:
```bash
# Install Python packages
pip install -r requirements.txt

# Install the browser component
playwright install chromium

# Run the script
python main.py
```

---

### 🎮 How to Use

1.  Once running, open the Gradio interface (usually `http://127.0.0.1:7860`).
2.  Navigate to the **Settings & Calibration** tab.
3.  Click **Take Screenshot**. Drag the sliders to position the Green Box over the proximity chat UI and the Red Box over the death screen notification text.
4.  Go to the **Dashboard** tab and click **START**.
5.  Play your game. The script will provide audio cues when it recognizes text in the defined regions.

---

### ⚠️ Disclaimer

This tool is an educational project that demonstrates the use of OCR in a real-time application.

*   ✅ It **only** reads pixels from your screen.
*   ❌ It **does not** read game memory, inject code, or interact with game files in any way.

This script is provided as-is. Use it at your own risk. Users are responsible for their own actions. **Do not use this tool to harass other players or violate any game's Terms of Service. Be a good human.**
