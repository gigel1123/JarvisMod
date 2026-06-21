# JarvisMod 🤖

A lightweight, user-friendly voice assistant built for ultimate flexibility and community-driven customization. JarvisMod features a modular core that allows developers and users to easily create, install, and share custom plugins.

---

## 🚀 Features

* **Modular Core:** Built from scratch to be minimal, fast, and completely unbloated.
* **Plugin-Focused Architecture:** Easily extend capabilities by dropping Python scripts into the `plugins/` directory.
* **Voice & GUI Driven:** Combines local voice processing with an intuitive user interface.
* **Local First:** Optimized to work efficiently using local tools and minimal API dependencies.

---

## 🛠️ Project Structure

* `jarvis.py` — The core logic, handling voice processing and orchestration.
* `gui.py` — The user interface layout and styling.
* `plugins/` — The dedicated folder where all custom and community plugins live.
* `mic_handling.py` & `talk.py` — Audio input and speech synthesis utilities.

---

## 🚀 Easy 1-Click Installation

1. **Download JarvisMod:** Click the green **Code** button at the top right of this page and select **Download ZIP**.
2. **Extract the ZIP:** Extract the folder to your Desktop.
3. **Run Setup:** Double-click **`JarvisMod_Setup.bat`**. It will automatically check for Python, install it if it's missing, configure your environment, and clean itself up.

Once finished, just double-click **`JarvisMod.bat`** to start talking to Jarvis!

## 🧩 Installing Community Plugins

Adding new capabilities to your assistant takes seconds:

1. Download a community-made plugin file (e.g., `weather_plugin.py`).
2. Drop the `.py` file straight into the `plugins/` folder inside your Jarvis directory.
3. Restart Jarvis and your new commands are ready to go!

---

### 🔌 Custom Plugin Template For Developers

To build a new plugin for JarvisMod, create a blank Python file in the `plugins/` directory (e.g., `my_plugin.py`) and copy/paste this boilerplate code. Just fill in your metadata and logic!

```python
"""
JarvisMod Plugin Template
Copy this file into the plugins/ folder to create custom functionality.
"""

# 1. Framework Metadata (Required)
# The unique command name users will say or type to trigger this plugin.
PLUGIN_NAME = "your_plugin_name"

# A brief description explaining what the plugin does and any arguments it takes.
PLUGIN_DESC = "your_plugin_name (argument: example) - Explains what your plugin does"


def run(*args):
    """
    The main execution loop called by the JarvisMod core.
    
    Parameters:
    *args: Dynamic tuple containing any text arguments passed by the user's input.
    
    Returns:
    str: A status message or response that Jarvis will display or speak back.
    """
    # Optional: Extract and validate arguments passed to the plugin
    if not args:
        return "Error: Missing required argument for this plugin."
        
    user_argument = args[0]

    # --- WRITE YOUR CUSTOM CODE HERE ---
    # Example: Processing a task, running a system command, fetching an API, etc.
    result = f"Successfully processed {user_argument}!"
    # -----------------------------------

    # Always return a string response for the framework to output
    return result
