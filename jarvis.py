import time
from logging import exception
import json
import pyautogui
import customtkinter as ctk
import customtkinter
import tkinter as tk
import os
import io
import ollama
from pynput import keyboard
import pynput
import sys
import PIL
import ctypes
from dotenv import load_dotenv
import threading
import urllib.parse
import webbrowser
from pynput.keyboard import Key, KeyCode
import queue
import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd
import whisper
import pyttsx3
from datetime import datetime
import subprocess
import base64

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

print("libraries loaded")

current_date_str = datetime.now().strftime("%A, %B %d, %Y")
date_injection = f"\n   IMPORTANT context: Today's date is {current_date_str}.\n"

project_root = r"C:\Users\Gaming\Desktop\Py\JARVIS\jarvis_code"
ffmpeg_bin_path = os.path.join(project_root, "bin")
ffmpeg_bin_path = os.path.join(project_root, "bin")
os.environ["PATH"] += os.pathsep + ffmpeg_bin_path

print("whisper env loaded")

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def jarvis_talk(response):
    talk = pyttsx3.init()
    talk.setProperty('rate', 175)
    talk.setProperty('volume', 1)
    talk.say(response)
    talk.runAndWait()

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# FUNCTIONS DOWN HERE
def question(answer):
    clean_text = str(answer)
    try:
        jarvis_talk(clean_text)
    except Exception as e:
        print(f"[DEBUG CRITICAL ERROR] Failed inside question tool wrapper: {e}")

print("jarvis_talk initialized")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#ANALYZE IMAGE
def ensure_ollama_ready(model_name="qwen2.5vl:3b"):
    """Ensures Ollama is running and responsive via clean pings."""
    print("Checking Ollama service status...")
    is_running = False
    try:
        with urllib.request.urlopen("http://localhost:11434", timeout=1.5) as response:
            if response.status == 200:
                is_running = True
    except Exception:
        pass

    if not is_running:
        print("Ollama is not running. Starting background service...")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        time.sleep(5)

    # Let's verify the model exists via a fast HTTP request
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            loaded_models = [m['name'] for m in data.get('models', [])]

        if not any(model_name in m for m in loaded_models):
            print(f"Model '{model_name}' not found locally. Pulling it now...")
            # Fire a pull command down to the engine
            pull_data = json.dumps({"name": model_name, "stream": False}).encode('utf-8')
            pull_req = urllib.request.Request(
                "http://localhost:11434/api/pull",
                data=pull_data,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(pull_req)
            print("Model pulled successfully!")
    except Exception as e:
        print(f"Setup warning: {e}")


def analyze_image():
    ensure_ollama_ready("qwen2.5vl:3b")

    print("Capturing screen...")
    screenshot = pyautogui.screenshot()

    # --- AGGRESSIVE INFERENCE OPTIMIZATION ---
    print("Compressing screenshot dimensions...")
    width, height = screenshot.size
    # Downscale to 50% size (massively drops processing overhead while keeping text readable)
    new_size = (int(width * 0.50), int(height * 0.50))
    optimized_image = screenshot.resize(new_size)

    # Save to memory as a highly compressed JPEG
    img_byte_arr = io.BytesIO()
    optimized_image.save(img_byte_arr, format="JPEG", quality=70)
    img_bytes = img_byte_arr.getvalue()
    # -----------------------------------------

    print("Encoding image to Base64...")
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')

    print("Sending request to Ollama (Inference active)...")

    payload = {
        "model": "qwen2.5vl:3b",
        "messages": [
            {
                "role": "user",
                "content": """You are a jarvis-like (iron man reference) bot and meant to help the user. 
                           DO NOT IN ANY CASE ADD TEXT THAT ISNT RAW JSON SUCH AS "I've got it!" or "I reccommend" or anything not JSON.
                           Adress the user as sir. Don't talk for too long and just be straight to the point
                           AND analyze the image as instructed -> Describe what is happening on this screen right 
                           now OR help with the question if there is any BUT do not talk to much. you should respond 
                           something that doesnt take anymore than 30 seconds to say in a natural tonel.""",
                "images": [img_b64]
            }
        ],
        "options": {
            "num_ctx": 4096  # Reduced context cap matches our new compressed token footprint perfectly
        },
        "stream": False,
        "keep_alive": -1  # PINS the model in your RAM/VRAM so subsequent calls take 2-3 seconds max!
    }

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )

        start_time = time.time()
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode())
            result = response_data['message']['content']

            elapsed = time.time() - start_time
            print(f"\n[Done in {elapsed:.2f}s] JARVIS Vision Output:\n{result}")
            jarvis_talk(result)
            return result

    except Exception as e:
        print(f"Inference failed: {e}")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def open_app(app_name):
    os.system(f"start {app_name}")
    jarvis_talk("Yes sir, opening now!")
    return f"attempted to open {app_name}"

print("open_app initialized")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def open_browser():
    webbrowser.open("google.com")

print("open_browser initialized")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def open_website(website_name):
    webbrowser.open(website_name)
    jarvis_talk("Yes sir, opening now!")

print("open_website initialized")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def give_answer(answer):
    jarvis_talk(answer)

print("give_answer initialized")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ACTIONS = {
    "analize_image": analyze_image,
    "open_app": open_app,
    "open_browser": open_browser,
    "open_website": open_website,
    "question": question,
}


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

print("ACTIONS defined")
print("Initiallizing Jarvis")

whisper_model = whisper.load_model("tiny")
SAMPLE_RATE = 16000
DURATION = 5
FILENAME = "command.wav"

def record_audio():
    audio_data = sd.rec(
        int(SAMPLE_RATE * DURATION),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16',
    )
    sd.wait()
    wav.write(FILENAME, SAMPLE_RATE, audio_data)

jarvis_start = False
voice_command = False
console_command = False

def get_voice_command():
    global voice_command
    voice_command = True
    record_audio()
    result = whisper_model.transcribe(FILENAME, fp16=False)
    text_command = result["text"].strip().lower()
    jarvis(text_command)
    if os.path.exists(FILENAME):
        os.remove(FILENAME)
    return text_command

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#INIT JARVIS

print("jarvis initialized")
print("whisper initialized")

CONVERSATION_HISTORY = []

system_prompt = """
   You are the reasoning engine for an automation framework named Jarvis.
   Analyze the user request and select the single best function to execute.
   User uses windows OS.
   For applications/websites/stuff with specific names make sure you give the correct agrument ( for example if user wants to open paint you give appname as mspaint).
   If the function says 'no argument' just respond with the function without specifying any argument. No argument means no argument. DO NOT PUT     "arguments": [""], just     "arguments": [].
   DO NOT DO ANYTHING BESIDES THESE INSTRUCTIONS!
   For example the user asks about whats on the screen, you would want to chose the analize_image function. 
   If user asks something or says hello or tries to make conversation rather than do a specific task, please chose the function 'question'.
   For the question fuction PLEASE use one single argument. the argument can be as long as you with and must contain the answer to the user input AND a salute to the user. For example if user asks for the date you lookup and give the answer.
   You must respond ONLY with a raw JSON object matching this schema:
   {
       "action": "function_name",
       "arguments": ["arg1", "arg2"]
   }

   Available functions:
   - "analize_image" (no argument)
   - "open_app" (argument: app_name)
   - "open_browser" (no arguments)
   - "open_website" (argument: website_name)
   - "question" (argument: salute the user and answer the questions.)
   """


def jarvis_init(user_input):
    global system_prompt
    global action_name
    global CONVERSATION_HISTORY

    # 1. Append user input to history tracking
    CONVERSATION_HISTORY.append({'role': 'user', 'content': user_input})

    try:
        # 2. Call your routing model and force it to stay in memory permanently
        response = ollama.chat(
            model='llama3',
            messages=CONVERSATION_HISTORY,
            options={
                "keep_alive": -1  # PINS llama3 into RAM/VRAM so it doesn't close!
            }
        )

        raw_out = response['message']['content'].strip()
        print(f"raw out:    {raw_out}")

        # Keep history synchronized
        CONVERSATION_HISTORY.append({'role': 'assistant', 'content': raw_out})

        # 3. Parse JSON decision format
        decision = json.loads(raw_out)
        print(f"decision: {decision}")

        action_name = decision.get("action")
        args = decision.get("arguments", [])
        print(f"action name: {action_name}")
        print(f"args: {args}")

        # 4. Trigger target tool
        if action_name in ACTIONS:
            # Executes the matched function dynamically matching your threading call
            result = ACTIONS[action_name](*args)
        else:
            print("ERROR: Unknown action")

    except json.JSONDecodeError:
        print("ERROR: Llama 3 output was not valid JSON text.")
    except Exception as e:
        print(f"ERROR: {e}")

full_prompt = system_prompt + date_injection
CONVERSATION_HISTORY = [{'role': 'system', 'content': full_prompt}]

print("jarvis_loop initialized")

def jarvis(user_input):
    ai_thread = threading.Thread(target=jarvis_init, args=(user_input,))
    ai_thread.daemon = False
    ai_thread.start()
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
get_voice_command()