import ctypes
from src import talk

def sleep_pc():
    print("Putting PC to sleep...")
    ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)

# plugins/test_plugin.py

# 1. The action name Jarvis and Llama 3 will use in the JSON payload
PLUGIN_NAME = "sleep_pc"

# 2. The instruction injected into the AI's system prompt telling it when to use this
PLUGIN_DESC = '"sleep_pc" (no arguments. Use this function when the user explicitly asks to put the pc to sleep mode)'

# 3. The actual function Jarvis executes when the action matches
def run():
    # Print to your console terminal
    print("\n[PLUGIN SUCCESS] The dynamic drop-in test plugin was called successfully!")

    # Make Jarvis speak to confirm it works
    talk.jarvis("Putting PC to sleep now sir!")
    sleep_pc()

    return "test plugin executed successfully"