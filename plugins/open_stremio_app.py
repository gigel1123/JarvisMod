import os
from src import talk

PLUGIN_NAME = "open_stremio_app"
PLUGIN_DESC = '"open_stremio_app" (no arguments. Use this function when asked to open stremio)'
# Keywords for instant bypass
KEYWORDS = ["open stremio", "start stremio", "play stremio"]

def run(*args):
    os.startfile("stremio.exe")
    print("\n[PLUGIN SUCCESS] Opening Stremio...")
    talk.jarvis("Yes sir! Opening stremio NOW!")
    return "stremio opened"