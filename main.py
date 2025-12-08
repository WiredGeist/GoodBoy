import gradio as gr
import cv2
import json
import time
import threading
import sys
import os
import re
import queue
import numpy as np
import sounddevice as sd
import mss
import scipy.signal
import pandas as pd
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from google import genai
from kittentts import KittenTTS
from rapidocr_onnxruntime import RapidOCR

# --- LOAD SECRETS ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# --- GLOBAL STATE ---
is_running = False
seen_players = {}
ocr_engine = None
tts_model = None
console_log = []
HISTORY_FILE = "daily_history.json"

# --- SEARCH QUEUE ---
search_queue = queue.Queue()

# Available Kitten Voices
KITTEN_VOICES = [
    'expr-voice-2-f', 'expr-voice-2-m', 
    'expr-voice-3-f', 'expr-voice-3-m',  
    'expr-voice-4-f', 'expr-voice-4-m', 
    'expr-voice-5-f', 'expr-voice-5-m'
]

# Default Config
DEFAULT_CONFIG = {
    "monitor_index": 1,
    "audio_device": 0,
    "tts_voice": "expr-voice-2-f", 
    "prox_x": 0, "prox_y": 730, "prox_w": 233, "prox_h": 152,
    "death_x": 990, "death_y": 580, "death_w": 600, "death_h": 300,
    "icon_crop": 65,
}

config = DEFAULT_CONFIG.copy()

# --- 1. CORE HELPERS ---

def load_config():
    global config
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r') as f:
                saved = json.load(f)
                config.update(saved)
        except: pass
    return config

def save_config_to_file():
    try:
        with open('config.json', 'w') as f:
            json.dump(config, f)
    except: pass

def load_history():
    global seen_players
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                seen_players = json.load(f)
        except: seen_players = {}
    return seen_players

def save_history_disk():
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(seen_players, f)
    except: pass

def update_player_data(name, status, details=None):
    if name not in seen_players:
        seen_players[name] = {"time": time.time(), "status": status, "details": details or "", "note": ""}
    else:
        seen_players[name]["time"] = time.time()
        seen_players[name]["status"] = status
        if details: seen_players[name]["details"] = details
    save_history_disk()

def add_user_note(name, note):
    if name in seen_players:
        seen_players[name]["note"] = note
        save_history_disk()
        log(f"Note added for {name}")
        return f"Saved note for {name}."
    else:
        seen_players[name] = {"time": time.time(), "status": "Manual Entry", "details": "", "note": note}
        save_history_disk()
        return f"Created entry for {name}."

def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    console_log.insert(0, entry)
    if len(console_log) > 50: console_log.pop()
    print(entry)
    return "\n".join(console_log)

def get_audio_devices():
    try:
        devices = sd.query_devices()
        device_list = []
        for i, d in enumerate(devices):
            if d['max_output_channels'] > 0:
                device_list.append(f"{i}: {d['name']}")
        return device_list
    except: return ["0: Default"]

def get_monitor_list():
    try:
        mon_list = []
        with mss.mss() as sct_temp:
            for i, m in enumerate(sct_temp.monitors):
                if i == 0: continue
                mon_list.append(f"{i}: {m['width']}x{m['height']} (Offset {m['left']},{m['top']})")
        return mon_list
    except: return ["1: Default"]

# --- 2. AI ENGINES & WORKER ---

def init_engines():
    global ocr_engine, tts_model
    if ocr_engine is None:
        log("Loading RapidOCR...")
        ocr_engine = RapidOCR()
    
    if tts_model is None:
        log("Loading KittenTTS...")
        try:
            tts_model = KittenTTS("KittenML/kitten-tts-nano-0.2")
            tts_model.generate("Warmup", voice=config.get("tts_voice", "expr-voice-2-f"))
        except Exception as e: log(f"TTS Error: {e}")

# --- WORKER THREAD ---
def queue_worker():
    while True:
        try:
            item = search_queue.get()
            if item is None: break 
            
            name, context = item
            check_bounty(name, context)
            
            search_queue.task_done()
        except Exception as e:
            print(f"Worker Error: {e}")

def speak(text):
    if not text: return
    text = re.sub(r'[*#_`\[\]]', '', text).strip()
    log(f"VOICE: {text}")
    
    def _speak_thread():
        try:
            if tts_model:
                selected_voice = config.get("tts_voice", "expr-voice-2-f")
                audio_24k = tts_model.generate(text, voice=selected_voice)
                
                target_rate = 48000
                samples = round(len(audio_24k) * float(target_rate) / 24000)
                audio_48k = scipy.signal.resample(audio_24k, samples)
                
                max_val = np.max(np.abs(audio_48k))
                if max_val > 0: audio_48k = audio_48k / max_val * 0.9 
                
                dev_idx = config.get("audio_device", 0)
                sd.play(audio_48k.astype(np.float32), target_rate, device=dev_idx, blocking=True, latency=0.3)
        except Exception as e:
            print(f"Audio Error: {e}")

    threading.Thread(target=_speak_thread, daemon=True).start()

def sanitize_website_content(text):
    garbage_phrases = [
        "Speranza Bounties is a community-driven platform",
        "TRACK • VOTE • ELIMINATE",
        "MARK TARGETS",
        "VOTE DAILY",
        "CONFIRM KILLS",
        "About Speranza Bounties",
        "FAQ",
        "Sign In",
        "Join Our Discord!",
        "Connect with the Speranza Bounties community",
        "Don't show this again",
        "JOIN DISCORD SERVER"
    ]
    for phrase in garbage_phrases:
        text = text.replace(phrase, "")
    return text

def check_bounty(player_name, context="Proximity"):
    log(f"Searching: {player_name}...")
    url = "https://speranzabounties.com/"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context_browser = browser.new_context()
            page = context_browser.new_page()
            
            # Allow images briefly so layout doesn't break, but block media
            page.route("**/*.{mp4,mp3}", lambda route: route.abort())
            
            page.goto(url)
            
            try:
                # NUKE POPUPS
                page.evaluate("""
                    document.querySelectorAll('div[class*="fixed"], div[class*="absolute"], div[class*="overlay"]').forEach(e => {
                        if (e.innerText.includes('Discord') || e.innerText.includes('Join')) {
                            e.remove();
                        }
                    });
                """)
                
                page.wait_for_timeout(1000)
                page.click('[placeholder="SEARCH TARGETS..."]', timeout=3000)
                page.keyboard.type(player_name, delay=50) 
                page.wait_for_timeout(200)
                page.keyboard.press('Enter')
                page.wait_for_timeout(3500)
                
            except Exception as e:
                print(f"Interaction Warning: {e}")
            
            raw_content = page.inner_text("body")
            clean_content = sanitize_website_content(raw_content)
            
            browser.close()

            if "NO TARGETS FOUND" in raw_content:
                log(f"Result: {player_name} is Clean.")
                update_player_data(player_name, "Clean", "No Record")
                speak(f"Raider {player_name} is not listed.")
            else:
                if GEMINI_KEY:
                    client = genai.Client(api_key=GEMINI_KEY)
                    
                    prompt = f"""
                    You are a tactical AI for Arc Raiders.
                    User searched for: '{player_name}'.
                    Raw Website Data: "{clean_content}"
                    
                    INSTRUCTIONS:
                    1. IGNORE the slogan "Track Vote Eliminate" and "Join Discord".
                    2. Look for SPECIFIC bounty tags (e.g. "Voice Chat Snake", "Extraction Camper").
                    3. If you see NO specific tags/stats for this player, reply: "Clean".
                    4. If there are tags, summarize them in 10 words.
                    5. Start the sentence with "{player_name} is listed for...".
                    6. Plain Text Only.
                    """
                    
                    try:
                        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt).text.strip()
                        
                        if "Clean" in response or "clean" in response:
                            update_player_data(player_name, "Clean", "Verified Clean")
                            speak(f"Raider {player_name} is not listed.")
                        else:
                            update_player_data(player_name, "Bounty", response)
                            speak(response)
                    except: 
                        update_player_data(player_name, "Bounty", "Manual Check Required")
                        speak(f"Warning. Bounty data found for {player_name}")
                else:
                    update_player_data(player_name, "Bounty", "No API Key")
                    speak(f"Warning. {player_name} has a record.")

    except Exception as e: log(f"Web Error: {e}")

# --- 3. VISION ---

def preprocess_image(img, is_prox=True):
    # Resize for better OCR
    img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    
    if is_prox:
        crop_val = config.get('icon_crop', 65)
        img = img[:, crop_val:] # Crop left icon
        if img.shape[2] == 4: img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        else: img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(img, 170, 255, cv2.THRESH_BINARY)
        return binary
    else:
        # Death screen: White text on Black BG -> Invert for OCR
        if img.shape[2] == 4: img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        else: img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.bitwise_not(img)
        _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
        return binary

def analyze_death_screen(ocr_results):
    killer_name = None
    sorted_lines = sorted(ocr_results, key=lambda x: x[0][0][1])
    trigger_index = -1
    
    for i, line in enumerate(sorted_lines):
        text = line[1].upper()
        if "KNOCKED" in text and "OUT" in text:
            trigger_index = i
            break
            
    if trigger_index != -1 and trigger_index + 1 < len(sorted_lines):
        next_line = sorted_lines[trigger_index + 1]
        raw_name = next_line[1]
        if "DAMAGE" in raw_name.upper() or "HEALTH" in raw_name.upper() or "ANVIL" in raw_name.upper():
            return None
        if len(raw_name) > 2:
            killer_name = raw_name

    return killer_name

# --- 4. BACKGROUND LOOP ---

def background_loop():
    global is_running, seen_players
    
    log("System Started.")
    init_engines()
    seen_players = load_history()
    
    # Start the Worker Thread (Daemon)
    threading.Thread(target=queue_worker, daemon=True).start()
    
    speak("Overlay Active.")
    
    while is_running:
        try:
            with mss.mss() as sct:
                monitor_idx = config.get("monitor_index", 1)
                
                # 1. Proximity
                mon_prox = {"top": config['prox_y'], "left": config['prox_x'], "width": config['prox_w'], "height": config['prox_h'], "mon": monitor_idx}
                img_prox = np.array(sct.grab(mon_prox))
                proc_prox = preprocess_image(img_prox, is_prox=True)
                res_prox, _ = ocr_engine(proc_prox)
                
                if res_prox:
                    for line in res_prox:
                        text, conf = line[1], line[2]
                        if conf > 0.6:
                            name = ''.join(e for e in text if e.isalnum() or e == '_')
                            if len(name) > 3 and name not in ["DETECTED", "SEARCHING", "Intel"]:
                                
                                # Re-encounter Logic
                                current_time = time.time()
                                needs_check = True
                                
                                if name in seen_players:
                                    last_time = seen_players[name].get("time", 0)
                                    if current_time - last_time < 1800: # 30 mins
                                        needs_check = False
                                    else:
                                        log(f"Re-encounter: {name}")
                                        status = seen_players[name].get("status", "Unknown")
                                        note = seen_players[name].get("note", "")
                                        msg = f"Re-encountering {name}."
                                        if status == "Clean": msg += " Still listed as Clean."
                                        elif status == "Bounty": msg += f" History says: {seen_players[name].get('details','')}"
                                        if note: msg += f" Your Note: {note}"
                                        
                                        speak(msg)
                                        seen_players[name]["time"] = current_time
                                        save_history_disk()
                                        needs_check = False

                                if needs_check:
                                    log(f"Queued: {name}")
                                    update_player_data(name, "Queued...") 
                                    search_queue.put((name, "Proximity"))

                # 2. Death Screen
                if int(time.time() * 10) % 5 == 0:
                    mon_death = {"top": config['death_y'], "left": config['death_x'], "width": config['death_w'], "height": config['death_h'], "mon": monitor_idx}
                    img_death = np.array(sct.grab(mon_death))
                    
                    proc_death = preprocess_image(img_death, is_prox=False)
                    res_death, _ = ocr_engine(proc_death)
                    
                    if res_death:
                        killer = analyze_death_screen(res_death)
                        if killer:
                            clean_killer = ''.join(e for e in killer if e.isalnum() or e == '_' or e == '-')
                            
                            if len(clean_killer) > 2:
                                need_scan = False
                                curr_t = time.time()
                                
                                if clean_killer not in seen_players:
                                    need_scan = True
                                else:
                                    last_t = seen_players[clean_killer].get("time", 0)
                                    if curr_t - last_t > 300: 
                                        need_scan = True

                                if need_scan:
                                    update_player_data(clean_killer, "Queued...", "Death Screen")
                                    log(f"KILLED BY: {clean_killer}")
                                    speak(f"Killed by {clean_killer}. Checking record.")
                                    search_queue.put((clean_killer, "Death"))

            time.sleep(0.5)
        except Exception as e:
            print(f"Loop Error: {e}")
            
    log("System Stopped.")

# --- 5. GUI FUNCTIONS ---

def toggle_system(running):
    global is_running
    if running and is_running: return "Running 🟢"
    if running and not is_running:
        is_running = True
        threading.Thread(target=background_loop, daemon=True).start()
        return "Running 🟢"
    elif not running:
        is_running = False
        return "Stopped 🔴"
    return "Running 🟢" if is_running else "Stopped 🔴"

def get_preview_img(mon_idx_str, prox_x, prox_y, prox_w, prox_h, death_x, death_y, death_w, death_h):
    try: mon_idx = int(mon_idx_str.split(":")[0])
    except: mon_idx = 1
    
    with mss.mss() as sct_prev:
        if mon_idx >= len(sct_prev.monitors): mon_idx = 1
        monitor = sct_prev.monitors[mon_idx]
        img = np.array(sct_prev.grab(monitor))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        
        cv2.rectangle(img, (prox_x, prox_y), (prox_x+prox_w, prox_y+prox_h), (0, 255, 0), 4)
        cv2.putText(img, "PROX CHAT", (prox_x, prox_y-10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)

        cv2.rectangle(img, (death_x, death_y), (death_x+death_w, death_y+death_h), (255, 0, 0), 4)
        cv2.putText(img, "DEATH SCREEN", (death_x, death_y-10), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 4)
        
        return cv2.resize(img, (0,0), fx=0.3, fy=0.3)

def save_settings(mon_str, aud_dev, voice_str, px, py, pw, ph, dx, dy, dw, dh, icrop):
    try: m_idx = int(mon_str.split(":")[0])
    except: m_idx = 1
    try: a_idx = int(aud_dev.split(":")[0])
    except: a_idx = 0
    
    config["monitor_index"] = m_idx
    config["audio_device"] = a_idx
    config["tts_voice"] = voice_str
    config["prox_x"] = px; config["prox_y"] = py; config["prox_w"] = pw; config["prox_h"] = ph
    config["death_x"] = dx; config["death_y"] = dy; config["death_w"] = dw; config["death_h"] = dh
    config["icon_crop"] = icrop
    save_config_to_file()
    return "Configuration Saved!"

def get_history_data():
    load_history()
    data = []
    for name, info in seen_players.items():
        if isinstance(info, dict):
            t_str = time.strftime('%H:%M:%S', time.localtime(info.get('time', 0)))
            ctx = info.get('status', 'Unknown')
            details = info.get('details', '')
            note = info.get('note', '')
        else:
            t_str = time.strftime('%H:%M:%S', time.localtime(info))
            ctx = "Unknown"
            details = ""
            note = ""
        data.append([t_str, name, ctx, details, note])
    data.reverse()
    return pd.DataFrame(data, columns=["Time", "Player", "Status", "Details", "My Notes"])

def clear_history_data():
    global seen_players
    seen_players = {}
    save_history_disk()
    return get_history_data()

def save_grid_changes(df):
    global seen_players
    if df is None or df.empty: return
    
    # Iterate over the rows of the edited dataframe
    for index, row in df.iterrows():
        name = row['Player']
        new_note = row['My Notes']
        
        # Update the main dictionary if the note changed
        if name in seen_players:
            # Only update if it's actually different to save disk writes
            if seen_players[name]['note'] != new_note:
                seen_players[name]['note'] = new_note
                save_history_disk()

def update_log_display():
    return "\n".join(console_log)

def check_status_on_load():
    return "Running 🟢" if is_running else "Stopped 🔴"

# --- 6. GRADIO LAYOUT ---

load_config() 

# Define Blue Theme
blue_theme = gr.themes.Default(
    primary_hue="blue", 
    secondary_hue="cyan"
)

# REMOVED theme=... FROM HERE
with gr.Blocks(title="DOOD BOY") as app:
    gr.Markdown("# 🐕 GOOD BOY")
    gr.Markdown("### Created by [WiredGeist](https://github.com/WiredGeist)")
    
    with gr.Tabs():
        # --- DASHBOARD ---
        with gr.Tab("Live Dashboard"):
            with gr.Row():
                btn_start = gr.Button("▶ START SYSTEM", variant="primary")
                btn_stop = gr.Button("⏹ STOP SYSTEM", variant="stop")
            
            status_indicator = gr.Label(value="Checking Status...", label="System Status")
            
            with gr.Row():
                with gr.Column(scale=1):
                    log_output = gr.Textbox(label="System Log", lines=15, interactive=False)
                
                with gr.Column(scale=2):
                    gr.Markdown("### 📝 Player Notes")
                    with gr.Row():
                        txt_player_name = gr.Textbox(label="Player Name")
                        txt_note = gr.Textbox(label="Note (e.g. 'Friendly', 'KOS')")
                        btn_add_note = gr.Button("Add/Update Note")
                    lbl_note_status = gr.Label(label="Note Status")
                    
                    gr.Markdown("### 📜 Session History")
                    with gr.Row():
                        btn_refresh = gr.Button("🔄 Refresh List", variant="secondary")
                    
                    history_df = gr.DataFrame(
                        headers=["Time", "Player", "Status", "Details", "My Notes"], 
                        interactive=True,
                        datatype=["str", "str", "str", "str", "str"]
                    )

                    history_df.change(save_grid_changes, inputs=history_df, outputs=None)

        # --- SETTINGS ---
        with gr.Tab("Settings & Calibration"):
            gr.Markdown("### ⚙️ General Setup")
            with gr.Row():
                dd_monitor = gr.Dropdown(choices=get_monitor_list(), label="Game Monitor", value=get_monitor_list()[0] if get_monitor_list() else None)
                dd_audio = gr.Dropdown(choices=get_audio_devices(), label="Output Device (Voicemeeter)", value=None)
                dd_voice = gr.Dropdown(choices=KITTEN_VOICES, label="AI Voice", value=config.get("tts_voice", "expr-voice-2-f"))
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🟩 Proximity Chat (Left)")
                    sl_px = gr.Slider(0, 2560, value=config["prox_x"], label="X Pos")
                    sl_py = gr.Slider(0, 1440, value=config["prox_y"], label="Y Pos")
                    sl_pw = gr.Slider(10, 500, value=config["prox_w"], label="Width")
                    sl_ph = gr.Slider(10, 200, value=config["prox_h"], label="Height")
                    sl_crop = gr.Slider(0, 100, value=config["icon_crop"], label="Icon Crop (Left)")
                
                with gr.Column():
                    gr.Markdown("### 🟥 Death Screen (Center)")
                    sl_dx = gr.Slider(0, 2560, value=config["death_x"], label="X Pos")
                    sl_dy = gr.Slider(0, 1440, value=config["death_y"], label="Y Pos")
                    sl_dw = gr.Slider(10, 800, value=config["death_w"], label="Width")
                    sl_dh = gr.Slider(10, 400, value=config["death_h"], label="Height")

            btn_preview = gr.Button("📸 Take Screenshot & Show Boxes")
            img_preview = gr.Image(label="Calibration Preview", interactive=False)
            
            btn_save = gr.Button("💾 Save Configuration", variant="primary")
            lbl_save = gr.Label(label="Last Action")
            
            gr.Markdown("### ⚠ Debugging Zone")
            with gr.Row():
                 btn_clear = gr.Button("🗑️ ERASE ALL HISTORY (Debug Only)", variant="stop")

    # --- EVENTS ---
    app.load(check_status_on_load, outputs=status_indicator)
    
    btn_start.click(lambda: toggle_system(True), outputs=status_indicator)
    btn_stop.click(lambda: toggle_system(False), outputs=status_indicator)
    
    timer_log = gr.Timer(1)
    timer_log.tick(update_log_display, outputs=log_output)
    
    btn_refresh.click(get_history_data, outputs=history_df)
    
    btn_clear.click(clear_history_data, outputs=history_df)
    
    btn_add_note.click(add_user_note, inputs=[txt_player_name, txt_note], outputs=lbl_note_status)
    
    btn_preview.click(get_preview_img, 
                      inputs=[dd_monitor, sl_px, sl_py, sl_pw, sl_ph, sl_dx, sl_dy, sl_dw, sl_dh],
                      outputs=img_preview)
    
    btn_save.click(save_settings,
                   inputs=[dd_monitor, dd_audio, dd_voice, sl_px, sl_py, sl_pw, sl_ph, sl_dx, sl_dy, sl_dw, sl_dh, sl_crop],
                   outputs=lbl_save)

if __name__ == "__main__":
    # ADDED THEME HERE
    app.launch(inbrowser=True, theme=blue_theme)