import tkinter as tk
from tkinter import ttk
import threading
import time
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Listener, KeyCode
# Ensure 'talk' is available in your sys.path
from src import talk

# --- Plugin Metadata (Updated to match test template) ---
PLUGIN_NAME = "auto_clicker"
PLUGIN_DESC = 'Opens the Auto Clicker GUI. Use F6 or "\\" to start/stop the clicking.'
KEYWORDS = ["activate auto clicker", "auto clicker", "open auto clicker"]

# --- Internal State ---
CLICKER_ACTIVE = False
MOUSE = MouseController()
CPS_OPTIONS = [1, 5, 10, 20, 50, 100, 250, 500, 1000, 2000]

def click_worker(cps, duration):
    global CLICKER_ACTIVE
    CLICKER_ACTIVE = True
    start_time = time.time()
    delay = 1.0 / cps if cps > 0 else 0

    while CLICKER_ACTIVE:
        if duration != "infinity" and (time.time() - start_time) > duration:
            break
        MOUSE.click(Button.left, 1)
        if delay > 0:
            time.sleep(delay)
    CLICKER_ACTIVE = False

def create_gui():
    root = tk.Tk()
    root.title("Auto Clicker")
    root.geometry("300x250")

    tk.Label(root, text="Select Speed (CPS):").pack(pady=(10, 0))
    cps_dropdown = ttk.Combobox(root, values=CPS_OPTIONS, state="readonly")
    cps_dropdown.current(2)
    cps_dropdown.pack(pady=5)

    tk.Label(root, text="Duration (seconds):").pack()
    dur_entry = tk.Entry(root)
    dur_entry.insert(0, "10")
    dur_entry.pack()

    infinite_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Click until stopped", variable=infinite_var).pack(pady=5)

    def on_press(key):
        global CLICKER_ACTIVE
        if key == KeyCode.from_vk(117) or (hasattr(key, 'char') and key.char == '\\'):
            if CLICKER_ACTIVE:
                CLICKER_ACTIVE = False
            else:
                try:
                    cps = int(cps_dropdown.get())
                    dur = "infinity" if infinite_var.get() else int(dur_entry.get())
                    threading.Thread(target=click_worker, args=(cps, dur), daemon=True).start()
                except ValueError:
                    pass

    listener = Listener(on_press=on_press)
    listener.daemon = True
    listener.start()
    root.mainloop()

# --- Main Entry Point ---
def run(*args):
    """
    Called by the plugin loader.
    """
    talk.jarvis("Opening auto clicker control panel.")

    # GUI must run on the main thread for Tkinter compatibility,
    # but the plugin loader runs in a worker thread.
    # If this fails, consider spawning a new process.
    try:
        # We invoke create_gui directly here
        create_gui()
        return "Auto-clicker GUI closed"
    except Exception as e:
        return f"Failed to open GUI: {e}"

if __name__ == "__main__":
    run()