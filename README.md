🐕 GOOD BOY
Created by WiredGeist

GOOD BOY is your tactical emotional support dog for Arc Raiders. He sits in the background, watches your screen, and barks (figuratively) when he sees a bad guy.

Basically, it reads names from Proximity Chat and your Death Screen, Googles them on the bounty database, and tells you if they are a friendly streamer or a toxic extraction camper using AI voice.

He protec, he attac, but mostly he reads text off your screen.
🦴 What does he do?

    Sniffs out Enemies: Uses OCR to read names from the proximity chat UI instantly.

    Revenge Mode: Reads the "KNOCKED OUT BY" screen (even with the inverted colors) so you know exactly who to hold a grudge against.

    The Gossip Protocol: Cross-references names with community bounty lists.

    AI Snitching: Uses Google Gemini AI to read the bounty reports and summarize exactly why that player is bad news (e.g., "Betrayer," "Loot Goblin") via TTS.

    No Crashes: Features a smart queue system. If 10 people rush you at once, GOOD BOY waits his turn to dox them one by one.

    Memory: Keeps a local history of everyone you've met. You can even write your own notes in the dashboard (like "This guy gave me a medkit" or "KOS").

🛠️ The Brains (Tech Stack)

    Interface: Gradio (Custom Blue/Cyan "Sci-Fi" Theme)

    Eyes: RapidOCR & OpenCV & MSS

    Legs: Playwright (for browsing the bounty site)

    Brain: Google Gemini 2.0 Flash

    Voice: KittenTTS

🚀 How to wake him up
1. Clone the repo
code Bash

    
git clone https://github.com/WiredGeist/good-boy-watchdog.git
cd good-boy-watchdog

  

2. Feed him requirements
code Bash

    
pip install -r requirements.txt

  

3. Install the browser stuff
code Bash

    
playwright install chromium

  

4. Give him a brain (API Key)

Create a .env file in the folder and add your Gemini key:
code Ini

    
GEMINI_API_KEY=your_key_goes_here

  

5. Let him run
code Bash

    
python main.py

  

🎮 How to use

    Open the link (usually http://127.0.0.1:7860).

    Go to Settings & Calibration.

    Click Take Screenshot. Move the sliders until the Green Box is over the Prox Chat names and the Red Box is over the Death Screen text.

    Go to Dashboard and click START.

    Play the game. Good Boy will speak to you when he finds intel.

⚠️ Disclaimer

This tool uses OCR (Optical Character Recognition) to look at your screen. It's essentially a fancy screenshot tool. It does not touch game memory or inject code.

However, use it at your own risk. I'm just a coder, not your lawyer.

Created by WiredGeist
