import subprocess
from src import talk

PLUGIN_NAME = "kill_process"
PLUGIN_DESC = '"kill_process" (argument: process_name) - Use this when the user wants to terminate a running program.'
KEYWORDS = ["kill", "stop", "close process"]


def run(*args):
    # If the keyword "kill" is used without a target, ask for clarification
    if not args or len(args) == 0:
        talk.jarvis("Which process would you like me to kill?")
        return

    process_name = args[0]

    # Simple logic to ensure the name has .exe
    if not process_name.lower().endswith(".exe"):
        process_name += ".exe"

    print(f"\n[PLUGIN] Attempting to terminate: {process_name}")

    # Use Windows taskkill command
    try:
        # /f forces the process to close, /im specifies the image name
        result = subprocess.run(["taskkill", "/f", "/im", process_name], capture_output=True, text=True)

        if result.returncode == 0:
            talk.jarvis(f"Successfully killed {process_name}, sir.")
        else:
            talk.jarvis(f"I couldn't find a process named {process_name}. Please check the name.")

    except Exception as e:
        print(f"Error killing process: {e}")
        talk.jarvis("I encountered an error while trying to stop that process.")

    return "kill process executed"