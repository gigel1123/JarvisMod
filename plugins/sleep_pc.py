import ctypes
from src import talk

def sleep_pc():
    ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)

PLUGIN_NAME = "sleep_pc"
PLUGIN_DESC = '"sleep_pc" (no arguments. Use this function when the user explicitly asks to put the pc to sleep mode)'
# Keywords for instant bypass
KEYWORDS = ["sleep pc", "go to sleep", "sleep mode"]

def run(*args):
    print("\n[PLUGIN SUCCESS] Sleeping PC...")
    talk.jarvis("Putting PC to sleep now sir!")
    sleep_pc()
    return "pc sleeping"