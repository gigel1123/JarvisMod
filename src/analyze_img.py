import ollama
import urllib.request
import subprocess
import io
import time
import json
import base64
import pyautogui
import os
import talk

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
            talk.jarvis(result)
            return result

    except Exception as e:
        print(f"Inference failed: {e}")