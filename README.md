# 🐕 Good Boy: An OCR & TTS Companion for Gaming
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
