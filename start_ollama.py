import subprocess
import time
import os
import ollama

def start_ollama():
    """Starts the Ollama server in the background."""
    print("Starting Ollama server...")

    # Determines the command based on OS (handles Windows 'ollama app' vs Mac/Linux CLI)
    # 'stdout=subprocess.DEVNULL' keeps your Python terminal clean
    if os.name == 'nt':  # Windows
        process = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:  # Mac / Linux
        process = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Give the server a few seconds to initialize and bind to the port
    time.sleep(3)
    return process