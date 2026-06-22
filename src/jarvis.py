import time
import json
import pyautogui
import os
import ollama
import sys
import threading
import urllib.parse
import webbrowser
import queue
import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd
import whisper
from datetime import datetime
import requests
from ddgs import DDGS
import analyze_img as aimg
import talk
import start_ollama as stollama
import importlib.util
import pathlib

print("libraries loaded")
stollama.start_ollama()
current_date_str = datetime.now().strftime("%A, %B %d, %Y")
date_injection = f"\n   IMPORTANT context: Today's date is {current_date_str}.\n"

current_file_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(current_file_dir) == "src":
    project_root = os.path.dirname(current_file_dir)
else:
    project_root = current_file_dir

ffmpeg_bin_path = os.path.join(project_root, "bin")
os.environ["PATH"] += os.pathsep + ffmpeg_bin_path

print(f"Project environment root loaded dynamically at: {project_root}")
print("whisper env loaded")

on_whisper_update = None
on_jarvis_update = None


def question(answer):
    clean_text = str(answer)
    try:
        talk.jarvis(clean_text)
    except Exception as e:
        print(f"[DEBUG CRITICAL ERROR] Failed inside question tool wrapper: {e}")


print("jarvis_talk initialized")


def open_app(app_name):
    os.system(f"start {app_name}")
    talk.jarvis("Yes sir, opening now!")
    return f"attempted to open {app_name}"


print("open_app initialized")


def open_website(website_name):
    webbrowser.open(website_name)
    talk.jarvis("Yes sir, opening now!")


print("open_website initialized")


def none():
    talk.jarvis("Sorry, this function doesn't exist or doesn't currently work! Please try again later!")


def take_screenshot():
    sc = pyautogui.screenshot()
    screenshot_path = os.path.join(project_root, "screenshot.png")
    sc.save(screenshot_path)


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


PLUGINS_DIR = os.path.abspath(os.path.join(project_root, "plugins"))
os.makedirs(PLUGINS_DIR, exist_ok=True)

json_path = os.path.join(project_root, "settings.json")
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
    "open_website": open_website if config.get("open_website", True) else none,
    "question": question if config.get("question", True) else none,
    "none": none,
    "screenshot": take_screenshot if config.get("screenshot", True) else none,
    "online_question": google_question if config.get("online_question", True) else none,
}

# Dictionary to hold the keyword mapping for instant execution bypass
KEYWORD_REGISTRY = {}


def load_plugins():
    global ACTIONS, KEYWORD_REGISTRY, config
    config_updated = False
    plugin_prompt_additions = ""
    KEYWORD_REGISTRY.clear()

    for core_action in ["analize_image", "open_app", "open_website", "question", "screenshot", "online_question"]:
        if core_action not in config:
            config[core_action] = True
            config_updated = True

    print("Checking for drop-in plugins...")

    present_plugins = set()
    if os.path.exists(PLUGINS_DIR):
        for file in os.listdir(PLUGINS_DIR):
            if file.endswith(".py") and file != "__init__.py":
                plugin_name = pathlib.Path(file).stem
                present_plugins.add(plugin_name)

                if plugin_name not in config:
                    config[plugin_name] = True
                    config_updated = True

                if not config[plugin_name]:
                    ACTIONS[plugin_name] = none
                    continue

                try:
                    file_path = os.path.join(PLUGINS_DIR, file)
                    spec = importlib.util.spec_from_file_location(plugin_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    act_name = getattr(module, "PLUGIN_NAME", plugin_name)
                    act_func = getattr(module, "run", None)
                    act_desc = getattr(module, "PLUGIN_DESC", f"- \"{act_name}\" (dynamically loaded custom action)")
                    act_keywords = getattr(module, "KEYWORDS", [])

                    if act_func:
                        ACTIONS[act_name] = act_func
                        plugin_prompt_additions += f"\n- {act_desc}"

                        # Register up to 3 valid keywords for AI bypass
                        registered_count = 0
                        for kw in act_keywords:
                            if registered_count >= 3:
                                break
                            clean_kw = str(kw).strip().lower()
                            if clean_kw:
                                KEYWORD_REGISTRY[clean_kw] = act_name
                                registered_count += 1

                        print(
                            f" Successfully loaded plugin tool: {act_name} (Registered {registered_count} bypass keywords)")
                    else:
                        print(f"⚠️ Failed to load {file}: Missing 'run(*args)' function entrypoint.")

                except Exception as e:
                    print(f"❌ Error compiling plugin execution on file {file}: {e}")

    for key in list(config.keys()):
        if key not in ["analize_image", "open_app", "open_website", "question", "screenshot", "online_question",
                       "none"]:
            if key not in present_plugins:
                config.pop(key, None)
                if key in ACTIONS:
                    ACTIONS.pop(key, None)
                config_updated = True

    if config_updated:
        with open(json_path, "w") as f:
            json.dump(config, f, indent=4)

    dynamic_system_prompt = f"""You are the reasoning engine for an automation framework named Jarvis on Windows.
Your primary task is to map user statements to the single best structural action function available.

CRITICAL PIPELINE EXECUTION INSTRUCTIONS:
1. Review the "INSTALLED PLUGINS AND CUSTOM ACTIONS" section below. If any plugin description matches the user's explicit intent (e.g., setting a timer, playing a game, checking a custom API), you MUST prioritize selecting that plugin over generic actions.
2. If the user is trying to have small talk, say hello, or ask generic questions that don't match any custom tool description, select "question".
3. When asked to open a specific desktop app use the function "open_app".
4. If a function says 'no argument' in its description, do not provide any strings inside the arguments array.
5. AGAIN!!!! ONLY AND ONLY RAW JSON OBJECT MATCHING THE SCHEMA! NOTHING ELSE!
6. You must respond ONLY with a raw JSON object matching this schema:
{{
    "action": "function_name",
    "arguments": ["arg1", "arg2"]
}}
DO NOT include any conversational text or formatting wrappers besides the raw JSON object.

### INSTALLED PLUGINS AND CUSTOM ACTIONS (HIGHEST PRIORITY):{plugin_prompt_additions}

### STANDARD ACTIONS:
- "analize_image" (no argument)
- "open_app" (argument: app_name)
- "open_website" (argument: website_name) -Youtube IS a website and not an app
- "question" (argument: response text containing the conversation answer)
- "none" (no argument)
- "screenshot" (no argument)
- "online_question" (argument: search query string)"""

    return dynamic_system_prompt


system_prompt = load_plugins()
full_prompt = system_prompt + date_injection
CONVERSATION_HISTORY = [{'role': 'system', 'content': full_prompt}]

print("ACTIONS defined")
print("Initiallizing Jarvis")

whisper_model = whisper.load_model("medium")
SAMPLE_RATE = 16000
FILENAME = os.path.join(project_root, "command.wav")


def record_audio():
    print("Listening for command...")
    chunk_size = 1024
    audio_blocks = []

    volume_threshold = 500
    silence_limit_seconds = 1.5
    max_listen_timeout = 10.0

    max_silence_chunks = int((silence_limit_seconds * SAMPLE_RATE) / chunk_size)
    max_timeout_chunks = int((max_listen_timeout * SAMPLE_RATE) / chunk_size)

    silence_chunks = 0
    chunks_recorded = 0
    has_spoken = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
        while True:
            block, overflowed = stream.read(chunk_size)
            audio_blocks.append(block)
            chunks_recorded += 1

            volume_norm = np.linalg.norm(block) / np.sqrt(chunk_size)

            if volume_norm > volume_threshold:
                if not has_spoken:
                    print("Speech detected...")
                has_spoken = True
                silence_chunks = 0
            else:
                if has_spoken:
                    silence_chunks += 1
                    if silence_chunks >= max_silence_chunks:
                        print("Finished speaking.")
                        break
                else:
                    if chunks_recorded >= max_timeout_chunks:
                        print("Listening timed out (no speech detected).")
                        break

    audio_data = np.concatenate(audio_blocks, axis=0)
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

    # INSTANT BYPASS CHECKER: Scan for exact keyword triggers first to completely bypass local AI processing.
    for keyword, linked_action in KEYWORD_REGISTRY.items():
        if keyword in user_input:
            print(
                f"⚡ [BYPASS ACTIVATED] Voice string matched keyword '{keyword}'. Directly executing '{linked_action}'.")
            if linked_action in ACTIONS:
                # Pass the raw text command string as a fallback argument if the plugin checks for inputs
                ACTIONS[linked_action](user_input)
                return
            else:
                print("ERROR: Linked action bypass target missing.")

    # Fallback to local AI logic pipeline if no registered keywords hit
    CONVERSATION_HISTORY.append({'role': 'user', 'content': user_input})

    try:
        response = ollama.chat(
            model='llama3',
            messages=CONVERSATION_HISTORY,
            options={"keep_alive": -1}
        )

        raw_out = response['message']['content'].strip()
        print(f"raw out:    {raw_out}")

        if on_jarvis_update:
            on_jarvis_update(raw_out)

        CONVERSATION_HISTORY.append({'role': 'assistant', 'content': raw_out})
        decision = json.loads(raw_out)

        action_name = decision.get("action")
        args = decision.get("arguments", [])

        if action_name in ACTIONS:
            ACTIONS[action_name](*args)
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