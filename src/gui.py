import os
import json
import customtkinter as ctk
import threading
import urllib.request
import jarvis as jarvis_engine
import mic_handling as wake_word_engine
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PluginStoreWindow(ctk.CTkToplevel):
    def __init__(self, parent_app):
        super().__init__()
        self.parent_app = parent_app
        self.title("Jarvis Plugin Downloader")
        self.geometry("500x550")
        self.attributes("-topmost", True)

        title_lbl = ctk.CTkLabel(self, text="Browse & Install Plugins", font=ctk.CTkFont(size=16, weight="bold"))
        title_lbl.pack(pady=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=450, height=420)
        self.scroll_frame.pack(pady=10, fill="both", expand=True, padx=15)

        # Status label to show loading or errors
        self.status_lbl = ctk.CTkLabel(self.scroll_frame, text="Fetching online repository directory...")
        self.status_lbl.pack(pady=20)

        # Run network request in a thread so the UI doesn't freeze
        threading.Thread(target=self.fetch_remote_plugins, daemon=True).start()

    def fetch_remote_plugins(self):
        repo_url = "https://api.github.com/repos/gigel1123/JarvisMod/contents/plugins"
        try:
            # GitHub API requires a User-Agent header or it rejects the request
            req = urllib.request.Request(repo_url, headers={'User-Agent': 'JarvisClient'})
            with urllib.request.urlopen(req) as response:
                files = json.loads(response.read().decode())

            # Remove the initial loading label
            self.status_lbl.destroy()

            # Filter for .py files
            plugin_files = [f for f in files if f.get("name", "").endswith(".py")]

            if not plugin_files:
                self.show_error("No plugins found in the repository folder.")
                return

            for plugin in plugin_files:
                self.parent_app.after(0, self.create_plugin_row, plugin)

        except Exception as e:
            self.show_error(f"Failed to connect: {str(e)}")

    def show_error(self, message):
        self.parent_app.after(0, lambda: self.status_lbl.configure(text=message, text_color="#FF5252"))

    def create_plugin_row(self, plugin_info):
        filename = plugin_info["name"]
        download_url = plugin_info["download_url"]

        # Check if plugin is already downloaded locally
        local_path = os.path.join("plugins", filename)
        is_installed = os.path.exists(local_path)

        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", pady=6, padx=5)

        # Clean display name (removing .py extension)
        display_name = filename.replace(".py", "").replace("_", " ").title()
        lbl = ctk.CTkLabel(frame, text=display_name, font=ctk.CTkFont(size=13, weight="bold"))
        lbl.pack(side="left", anchor="w")

        # Setup action button
        btn = ctk.CTkButton(frame, width=90)
        if is_installed:
            btn.configure(text="Installed", state="disabled", fg_color="#2E7D32")
        else:
            btn.configure(text="Install", command=lambda: self.start_download(filename, download_url, btn))

        btn.pack(side="right", anchor="e")

    def start_download(self, filename, url, button_widget):
        button_widget.configure(text="Downloading...", state="disabled", fg_color="#EF6C00")
        threading.Thread(target=self.download_worker, args=(filename, url, button_widget), daemon=True).start()

    def download_worker(self, filename, url, button_widget):
        try:
            # Ensure the local plugins folder actually exists
            os.makedirs("plugins", exist_ok=True)
            local_path = os.path.join("plugins", filename)

            # Request and stream file data locally
            req = urllib.request.Request(url, headers={'User-Agent': 'JarvisClient'})
            with urllib.request.urlopen(req) as response, open(local_path, 'wb') as out_file:
                out_file.write(response.read())

            # Update UI on success
            self.parent_app.after(0, lambda: button_widget.configure(text="Installed", fg_color="#2E7D32"))

            # Re-compile settings in memory so the toggle list registers the fresh plug-in
            jarvis_engine.load_plugins()
            self.parent_app.refresh_actions_on_toggle()

        except Exception as e:
            self.parent_app.after(0, lambda: button_widget.configure(text="Retry", state="normal", fg_color="#D32F2F"))


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent_app):
        super().__init__()
        self.parent_app = parent_app
        self.title("Jarvis Settings Manager")
        self.geometry("450x550")
        self.attributes("-topmost", True)

        title_lbl = ctk.CTkLabel(self, text="Toggle Functions & Plugins", font=ctk.CTkFont(size=16, weight="bold"))
        title_lbl.pack(pady=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=400, height=420)
        self.scroll_frame.pack(pady=10, fill="both", expand=True, padx=15)

        self.switches = {}
        self.load_toggles()

    def load_toggles(self):
        if os.path.exists(jarvis_engine.json_path):
            with open(jarvis_engine.json_path, "r") as f:
                try:
                    jarvis_engine.config = json.load(f)
                except json.JSONDecodeError:
                    pass

        for key, value in jarvis_engine.config.items():
            frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            frame.pack(fill="x", pady=5, padx=5)

            lbl = ctk.CTkLabel(frame, text=key, font=ctk.CTkFont(size=13))
            lbl.pack(side="left", anchor="w")

            switch_var = ctk.BooleanVar(value=value)
            switch = ctk.CTkSwitch(
                frame,
                text="",
                variable=switch_var,
                command=lambda k=key, v=switch_var: self.toggle_setting(k, v)
            )
            switch.pack(side="right", anchor="e")
            self.switches[key] = switch_var

    def toggle_setting(self, key, var_value):
        current_state = var_value.get()
        jarvis_engine.config[key] = current_state

        with open(jarvis_engine.json_path, "w") as f:
            json.dump(jarvis_engine.config, f, indent=4)

        if not current_state:
            jarvis_engine.ACTIONS[key] = jarvis_engine.none
        else:
            CORE_MAPPING = {
                "analize_image": jarvis_engine.aimg.analyze_image if hasattr(jarvis_engine,
                                                                             'aimg') else jarvis_engine.none,
                "open_app": jarvis_engine.open_app,
                "open_browser": jarvis_engine.open_browser,
                "open_website": jarvis_engine.open_website,
                "question": jarvis_engine.question,
                "none": jarvis_engine.none,
                "screenshot": jarvis_engine.take_screenshot,
                "online_question": jarvis_engine.google_question,
                "play_track": jarvis_engine.spotify_control.search_and_play if hasattr(jarvis_engine,
                                                                                       'spotify_control') else jarvis_engine.none,
                "next_track": jarvis_engine.next_track,
                "previous_track": jarvis_engine.previous_track,
                "pause_track": jarvis_engine.pause_track,
                "unpause_track": jarvis_engine.unpause_track,
            }

            if key in CORE_MAPPING:
                jarvis_engine.ACTIONS[key] = CORE_MAPPING[key]
            else:
                jarvis_engine.load_plugins()

            self.parent_app.refresh_actions_on_toggle()


class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jarvis Workspace Console")
        self.geometry("650x570")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.settings_window = None
        self.store_window = None

        # Top Frame Area
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=15)

        self.title_lbl = ctk.CTkLabel(self.top_frame, text="JARVIS AUTOMATION CONSOLE",
                                      font=ctk.CTkFont(size=18, weight="bold"))
        self.title_lbl.pack(side="left")

        # Container Frame for action buttons to look neat together
        self.btn_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.btn_frame.pack(side="right")

        self.store_btn = ctk.CTkButton(self.btn_frame, text="🔌 Plugin Store", width=110, command=self.open_store)
        self.store_btn.pack(side="left", padx=(0, 5))

        self.settings_btn = ctk.CTkButton(self.btn_frame, text="⚙ Settings", width=110, command=self.open_settings)
        self.settings_btn.pack(side="left")

        # Whisper Output Panel
        self.whisper_lbl = ctk.CTkLabel(self, text="Whisper Speech Transcript:", font=ctk.CTkFont(weight="bold"))
        self.whisper_lbl.pack(anchor="w", padx=20, pady=(5, 2))
        self.whisper_text = ctk.CTkTextbox(self, height=70, activate_scrollbars=True)
        self.whisper_text.pack(fill="x", padx=20)
        self.whisper_text.insert("0.0", "Awaiting wake word command entry...")

        # Jarvis Processing Panel
        self.jarvis_lbl = ctk.CTkLabel(self, text="Jarvis Framework Core Output:", font=ctk.CTkFont(weight="bold"))
        self.jarvis_lbl.pack(anchor="w", padx=20, pady=(15, 2))
        self.jarvis_text = ctk.CTkTextbox(self, height=130, activate_scrollbars=True)
        self.jarvis_text.pack(fill="x", padx=20)
        self.jarvis_text.insert("0.0", "Systems Idle.")

        # Manual Override Input field
        self.prompt_lbl = ctk.CTkLabel(self, text="Manual Execution Terminal Override:",
                                       font=ctk.CTkFont(weight="bold"))
        self.prompt_lbl.pack(anchor="w", padx=20, pady=(15, 2))

        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.entry_field = ctk.CTkEntry(self.input_frame, placeholder_text="Type custom terminal commands here...")
        self.entry_field.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_field.bind("<Return>", lambda event: self.send_manual_prompt())

        self.send_btn = ctk.CTkButton(self.input_frame, text="Execute", width=100, command=self.send_manual_prompt)
        self.send_btn.pack(side="right")

        # Live Engine Status Display
        self.status_lbl = ctk.CTkLabel(self, text="🟢 Wake Word Engine Active: Sleep Mode ('Hey Jarvis')",
                                       text_color="#4CAF50", font=ctk.CTkFont(weight="bold"))
        self.status_lbl.pack(pady=(0, 15))

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()

    def open_store(self):
        if self.store_window is None or not self.store_window.winfo_exists():
            self.store_window = PluginStoreWindow(self)
        else:
            self.store_window.focus()

    def refresh_actions_on_toggle(self):
        jarvis_engine.system_prompt = jarvis_engine.load_plugins()
        jarvis_engine.full_prompt = jarvis_engine.system_prompt + jarvis_engine.date_injection
        if jarvis_engine.CONVERSATION_HISTORY:
            jarvis_engine.CONVERSATION_HISTORY[0] = {'role': 'system', 'content': jarvis_engine.full_prompt}

    def update_whisper_ui(self, text):
        self.whisper_text.delete("1.0", "end")
        self.whisper_text.insert("1.0", text)

    def update_jarvis_ui(self, raw_json_or_status):
        self.jarvis_text.delete("1.0", "end")
        self.jarvis_text.insert("1.0", raw_json_or_status)

    def update_status_indicator(self, msg, color_hex):
        self.status_lbl.configure(text=msg, text_color=color_hex)

    def send_manual_prompt(self):
        user_input = self.entry_field.get().strip()
        if user_input:
            self.update_whisper_ui(f"[Manual Input Override]: {user_input}")
            self.update_jarvis_ui("Sending request path directly to reasoning engine...")
            self.entry_field.delete(0, "end")
            jarvis_engine.jarvis(user_input)


if __name__ == "__main__":
    app = JarvisApp()

    jarvis_engine.on_whisper_update = app.update_whisper_ui
    jarvis_engine.on_jarvis_update = app.update_jarvis_ui
    wake_word_engine.on_status_msg_change = app.update_status_indicator

    mic_thread = threading.Thread(target=wake_word_engine.run_wake_word_engine, daemon=True)
    mic_thread.start()

    app.mainloop()