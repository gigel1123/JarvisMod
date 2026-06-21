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
import requests
from ddgs import DDGS
from spotify_local import SpotifyLocal
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import psutil
import shutil
import check_app as ca
import analyze_img as aimg
import talk
import spotify_control
import start_ollama as stollama
import importlib.util
import pathlib

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

print("libraries loaded")
stollama.start_ollama()
current_date_str = datetime.now().strftime("%A, %B %d, %Y")
date_injection = f"\n   IMPORTANT context: Today's date is {current_date_str}.\n"

project_root = r"C:\Users\Gaming\Desktop\Py\JARVIS\JARVIS"
ffmpeg_bin_path = os.path.join(project_root, "bin")
os.environ["PATH"] += os.pathsep + ffmpeg_bin_path

print("whisper env loaded")

# GUI Thread Hooks (Placeholders for UI updates to completely prevent circular imports)
on_whisper_update = None
on_jarvis_update = None


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# FUNCTIONS DOWN HERE
def question(answer):
    clean_text = str(answer)
    try:
        talk.jarvis(clean_text)
    except Exception as e:
        print(f"[DEBUG CRITICAL ERROR] Failed inside question tool wrapper: {e}")


print("jarvis_talk initialized")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def open_app(app_name):
    os.system(f"start {app_name}")
    talk.jarvis("Yes sir, opening now!")
    return f"attempted to open {app_name}"


print("open_app initialized")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def open_browser():
    webbrowser.open("google.com")


print("open_browser initialized")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def open_website(website_name):
    webbrowser.open(website_name)
    talk.jarvis("Yes sir, opening now!")


print("open_website initialized")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def give_answer(answer):
    talk.jarvis(answer)


print("give_answer initialized")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def none():
    talk.jarvis("Sorry, this function doesn't exist or doesn't currently work! Please try again later!")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def take_screenshot():
    sc = pyautogui.screenshot()
    sc.save("screenshot.png")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def google_question(query: str):
    print(f"🤖 Jarvis is searching the web for: {query}...")

    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
    except Exception as e:
        return f"Failed to fetch search results: {e}"

    if not results:
        return "No search results found."

    web_context = ""
    for i, result in enumerate(results):
        web_context += f"Source [{i + 1}]: {result['title']}\nSnippet: {result['body']}\n\n"

    ollama_prompt = f"""
    You are Jarvis. Answer the user's question using the provided web search context. 
    Be concise, conversational, and direct.

    User Question: {query}

    Web Context:
    {web_context}
    """

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": ollama_prompt,
                "stream": False
            }
        )
        return response.json().get("response", "Error parsing Ollama response.")
    except Exception as e:
        return f"Local Ollama connection failed: {e}"


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def next_track():
    with SpotifyLocal() as sp:
        sp.next()


def previous_track():
    with SpotifyLocal() as sp:
        sp.previous()


def pause_track():
    with SpotifyLocal() as sp:
        sp.pause()


def unpause_track():
    with SpotifyLocal() as sp:
        sp.unpause()


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

PLUGINS_DIR = os.path.join(project_root, "plugins")
os.makedirs(PLUGINS_DIR, exist_ok=True)

json_path = "settings.json"
if os.path.exists(json_path):
    with open(json_path, "r") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            config = {}
else:
    config = {}

ACTIONS = {
    "analize_image": aimg.analyze_image if config.get("analize_image", True) else none,
    "open_app": open_app if config.get("open_app", True) else none,
    "open_browser": open_browser if config.get("open_browser", True) else none,
    "open_website": open_website if config.get("open_website", True) else none,
    "question": question if config.get("question", True) else none,
    "none": none if config.get("none", True) else none,
    "screenshot": take_screenshot if config.get("screenshot", True) else none,
    "online_question": google_question if config.get("online_question", True) else none,
    "play_track": spotify_control.search_and_play if config.get("play_track", True) else none,
    "next_track": next_track if config.get("next_track", True) else none,
    "previous_track": previous_track if config.get("previous_track", True) else none,
    "pause_track": pause_track if config.get("pause_track", True) else none,
    "unpause_track": unpause_track if config.get("unpause_track", True) else none,
}

BASE_SYSTEM_PROMPT = """
You are the reasoning engine for an automation framework named Jarvis.
Analyze the user request and select the single best function to execute.
User uses windows OS.
For applications/websites/stuff with specific names make sure you give the correct agrument ( for example if user wants to open paint you give appname as mspaint).
When asked to open a specific app use the function open_app.
If the function says 'no argument' just respond with the function without specifying any argument. No argument means no argument. DO NOT PUT "arguments": [""], just "arguments": [].
DO NOT DO ANYTHING BESIDES THESE INSTRUCTIONS!
For example the user asks about whats on the screen, you would want to chose the analize_image function. 
If user asks something or says hello or tries to make conversation rather than do a specific task, please chose the function 'question'.
For the question function PLEASE use one single argument. the argument can be as long as you with and must contain the answer to the user input AND a salute to the user. For example if user asks for the date you lookup and give the answer.
If you dont understand the user input or dont know/have what function to chose PLEASE chose the function "none" as it is meant for when theres no specific function.
The "online_question" function is meant for questions that you don't know or require online knowledge.
The "question" function is meant for simple questions like basic multiplication in maths or stuff you already know without searching for the internet.
If there is a typo or something wrong in the input please chose the action none and dont say anything else.
The track functions are used for media control (for music).
When asked to 'unpause' or 'resume' assume its for 'unpause_track' function.
When asked to 'pause' or 'pause the music' or 'stop' or 'stop the music' assume its for 'pause_track' function.
When asked 'next' or 'next song' or 'play next song' assume its for 'next_track' function.
When asked 'previous' or 'previous song' assume its for 'previous_track' function.
When asked to 'Play' you would assume its to play music, so you will chose the 'play_track' function and specify the song name. 
If one single argument is needed then do not separate the string with a ",". You may use one single string in the argument, for examnple: "Let's go! May the adventure begin! Where are you headed?, Have a safe and exciting journey!" for function question.
AGAIN RESPLOND ONLY RAW JASON OBJECT MATCHIUNG THE GIVEN SCHEMA.
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
- "none" (no argument)
- "screenshot" (no argument)
- "online_question" (argument: what answer to search for online)
- "pause_track" (no arguments)
- "unpause_track" (no arguments)
- "play_track" (song name)
- "next_track" (no arguments)
- "previous_track" (no arguments)"""


def load_plugins():
    global BASE_SYSTEM_PROMPT, ACTIONS, config
    config_updated = False
    plugin_prompt_additions = ""

    for core_action in ["analize_image", "open_app", "open_browser", "open_website", "question", "none", "screenshot",
                        "online_question", "play_track", "next_track", "previous_track", "pause_track",
                        "unpause_track"]:
        if core_action not in config:
            config[core_action] = True
            config_updated = True

    print("Checking for drop-in plugins...")

    for file in os.listdir(PLUGINS_DIR):
        if file.endswith(".py") and file != "__init__.py":
            plugin_name = pathlib.Path(file).stem
            file_path = os.path.join(PLUGINS_DIR, file)

            if plugin_name not in config:
                config[plugin_name] = True
                config_updated = True

            if not config[plugin_name]:
                continue

            try:
                spec = importlib.util.spec_from_file_location(plugin_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                act_name = getattr(module, "PLUGIN_NAME", plugin_name)
                act_func = getattr(module, "run", None)
                act_desc = getattr(module, "PLUGIN_DESC", f"- \"{act_name}\" (dynamically loaded custom action)")

                if act_func:
                    ACTIONS[act_name] = act_func
                    plugin_prompt_additions += f"\n- {act_desc}"
                    print(f" Successfully loaded plugin tool: {act_name}")
                else:
                    print(f"⚠️ Failed to load {file}: Missing 'run(*args)' function entrypoint.")

            except Exception as e:
                print(f"❌ Error compiling plugin execution on file {file}: {e}")

    if config_updated:
        with open(json_path, "w") as f:
            json.dump(config, f, indent=4)

    return BASE_SYSTEM_PROMPT + plugin_prompt_additions


system_prompt = load_plugins()
full_prompt = system_prompt + date_injection
CONVERSATION_HISTORY = [{'role': 'system', 'content': full_prompt}]

print("ACTIONS defined")
print("Initiallizing Jarvis")

whisper_model = whisper.load_model("medium")
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

    # Notify GUI what Whisper extracted from the audio file
    if on_whisper_update:
        on_whisper_update(text_command)

    jarvis(text_command)
    if os.path.exists(FILENAME):
        os.remove(FILENAME)
    return text_command


print("jarvis initialized")
print("whisper initialized")


def jarvis_init(user_input):
    global system_prompt, action_name, CONVERSATION_HISTORY

    CONVERSATION_HISTORY.append({'role': 'user', 'content': user_input})

    try:
        response = ollama.chat(
            model='llama3',
            messages=CONVERSATION_HISTORY,
            options={"keep_alive": -1}
        )

        raw_out = response['message']['content'].strip()
        print(f"raw out:    {raw_out}")

        # Send raw inference details straight onto GUI interface screen
        if on_jarvis_update:
            on_jarvis_update(raw_out)

        CONVERSATION_HISTORY.append({'role': 'assistant', 'content': raw_out})
        decision = json.loads(raw_out)

        action_name = decision.get("action")
        args = decision.get("arguments", [])

        if action_name in ACTIONS:
            result = ACTIONS[action_name](*args)
        else:
            print("ERROR: Unknown action")

    except json.JSONDecodeError:
        if on_jarvis_update:
            on_jarvis_update("ERROR: Llama 3 output was not valid JSON text.")
    except Exception as e:
        talk.jarvis("ERROR. Something went wrong.")
        if on_jarvis_update:
            on_jarvis_update(f"ERROR: {e}")


print("jarvis_loop initialized")


def jarvis(user_input):
    ai_thread = threading.Thread(target=jarvis_init, args=(user_input,))
    ai_thread.daemon = True
    ai_thread.start()