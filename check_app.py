import json
import os
import shutil
import subprocess
import psutil

CONFIG_FILE = "config.json"

# ==============================================================================
# 1. THE APP REGISTRY
# Add any apps your project needs here. Use %ENVIRONMENT_VARIABLES% for paths.
# ==============================================================================
APP_REGISTRY = {
    "discord": {
        "process_name": "Discord.exe",
        "common_paths": [
            r"%LOCALAPPDATA%\Discord\Update.exe",
            r"%PROGRAMFILES%\Discord\Discord.exe",
        ],
    },
    "chrome": {
        "process_name": "chrome.exe",
        "common_paths": [
            r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
            r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe",
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
        ],
    },
    "notepad": {
        "process_name": "notepad.exe",
        "common_paths": [
            r"%WINDIR%\System32\notepad.exe",
        ],
    },
    "spotify": {
        "process_name": "Spotify.exe",
        "common_paths": [
            # Option A: Standard installer from the website
            r"%APPDATA%\Spotify\Spotify.exe",
            r"%LOCALAPPDATA%\Microsoft\WindowsApps\Spotify.exe",

            # Option B: Microsoft Store version fallback links
            r"%PROGRAMFILES%\WindowsApps\SpotifyAB.SpotifyMusic_*\Spotify.exe"
        ]
    }
}

# ==============================================================================
# 2. CONFIGURATION HELPERS
# ==============================================================================


def load_config():
    """Loads saved paths from the local config file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(config):
    """Saves paths to the local config file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


# ==============================================================================
# 3. CORE LOGIC
# ==============================================================================


def smart_launch(app_key):
    """Checks if an app is running, automatically locates its path, or asks

    the user as a fallback.
    """
    if app_key not in APP_REGISTRY:
        print(f"[-] Error: '{app_key}' is not defined in the APP_REGISTRY.")
        return

    process_name = APP_REGISTRY[app_key]["process_name"]
    common_paths = APP_REGISTRY[app_key]["common_paths"]

    # --- STEP 1: Check if the app is already running ---
    for proc in psutil.process_iter(["name"]):
        try:
            if process_name.lower() in proc.info["name"].lower():
                print(f"[+] '{process_name}' is already running.")
                return True
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            pass

    # --- STEP 2: Check the saved configuration file ---
    config = load_config()
    if app_key in config and os.path.exists(config[app_key]):
        print(f"[+] Launching {app_key} from saved configuration...")
        subprocess.Popen(config[app_key])
        return True

    # --- STEP 3: Check system environment PATH (e.g., shorthand commands) ---
    system_path = shutil.which(process_name)
    if system_path:
        print(f"[+] Found {process_name} on system PATH. Launching...")
        subprocess.Popen(system_path)
        return True

    # --- STEP 4: Scan common standard paths ---
    for path in common_paths:
        # os.path.expandvars converts things like %LOCALAPPDATA% to the real path
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            print(f"[+] Found {process_name} at: {expanded_path}. Launching...")
            subprocess.Popen(expanded_path)

            # Cache the path so we don't have to scan next time
            config[app_key] = expanded_path
            save_config(config)
            return True

    # --- STEP 5: Fallback User Prompt ---
    print(f"\n[!] Could not locate {process_name} automatically.")
    print(
        f"    This could be due to a custom installation drive (e.g., D:\\ or E:\\)."
    )
    user_path = input(
        f"    Please paste the absolute path to {process_name}: "
    ).strip('"')

    if os.path.exists(user_path):
        print(f"[+] Path verified. Launching and saving choice...")
        subprocess.Popen(user_path)

        # Save it to config so the prompt never happens again
        config[app_key] = user_path
        save_config(config)
        return True
    else:
        print(f"[-] Error: The path '{user_path}' does not exist. Aborting.")
        return False


# ==============================================================================
# 4. EXECUTION EXAMPLE
# ==============================================================================
if __name__ == "__main__":
    print("--- Testing App Launcher ---")

    # Example 1: Launch Notepad (Will usually be found on System PATH instantly)
    smart_launch("spotify")

    # Example 2: Launch Discord (Will usually be found via %LOCALAPPDATA%)
    # smart_launch("discord")