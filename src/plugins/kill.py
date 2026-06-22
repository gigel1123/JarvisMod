import psutil

# Define the metadata your framework uses (optional, but good practice)
PLUGIN_NAME = "kill_app"
PLUGIN_DESC = "kill_app (argument: app_name) - To close/kill a process. used when user asks to kill/close process/app"


def run(*args):
    """
    This is the entrypoint your Jarvis framework looks for.
    """
    if not args:
        print("No application name provided to kill.")
        return "Error: Missing application name argument."

    app_name = args[0]
    killed_any = False

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Check if the process name matches (case-insensitive)
            if app_name.lower() in proc.info['name'].lower():
                print(f"Jarvis Framework: Killing {proc.info['name']} (PID: {proc.info['pid']})...")
                proc.terminate()  # Soft close
                killed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if killed_any:
        return f"Successfully terminated processes matching '{app_name}'."
    else:
        return f"No active applications found matching '{app_name}'."
