# plugins/test_plugin.py
import os
from src import talk
# 1. The action name Jarvis and Llama 3 will use in the JSON payload
PLUGIN_NAME = "open_stremio_app"

# 2. The instruction injected into the AI's system prompt telling it when to use this
PLUGIN_DESC = '"open_stremio_app" (no arguments. Use this function when asked to open stremio which is an app but you will use specifically open stremio for this app and not open app!)'


# 3. The actual function Jarvis executes when the action matches
def run():
    os.startfile("stremio.exe")
    # Print to your console terminal
    print("\n[PLUGIN SUCCESS] The dynamic drop-in test plugin was called successfully!")

    # Make Jarvis speak to confirm it works
    talk.jarvis("Yes sir! Opening stremio NOW!")

    return "test plugin executed successfully"
