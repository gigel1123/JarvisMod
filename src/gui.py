import os
import json
import customtkinter as ctk
import threading
import urllib.request
import sys
import zipfile
import io
import shutil
import tempfile

import jarvis as jarvis_engine
import mic_handling as wake_word_engine

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# App Paths
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)
VERSION_FILE = os.path.join(SRC_DIR, "version.txt")
REPO_URL = "https://api.github.com/repos/gigel1123/JarvisMod"


class VersionWindow(ctk.CTkToplevel):
    def __init__(self, parent_app):
        super().__init__()
        self.parent_app = parent_app
        self.title("Jarvis Version Manager")
        self.geometry("500x450")
        self.attributes("-topmost", True)

        title_lbl = ctk.CTkLabel(self, text="Available Releases", font=ctk.CTkFont(size=16, weight="bold"))
        title_lbl.pack(pady=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=450, height=350)
        self.scroll_frame.pack(pady=10, fill="both", expand=True, padx=15)

        self.status_lbl = ctk.CTkLabel(self.scroll_frame, text="Fetching GitHub releases...")
        self.status_lbl.pack(pady=20)

        threading.Thread(target=self.fetch_releases, daemon=True).start()

    def fetch_releases(self):
        try:
            req = urllib.request.Request(f"{REPO_URL}/releases", headers={'User-Agent': 'JarvisClient'})
            with urllib.request.urlopen(req) as response:
                releases = json.loads(response.read().decode())

            self.status_lbl.destroy()

            if not releases:
                self.show_error("No releases found on GitHub.")
                return

            for release in releases:
                self.parent_app.after(0, self.create_release_row, release)

        except Exception as e:
            self.show_error(f"Failed to connect: {str(e)}")

    def show_error(self, message):
        self.parent_app.after(0, lambda: self.status_lbl.configure(text=message, text_color="#FF5252"))

    def create_release_row(self, release):
        tag_name = release.get("tag_name", "Unknown")
        zipball_url = release.get("zipball_url")

        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", pady=6, padx=5)

        lbl_text = f"{tag_name}"
        if tag_name == self.parent_app.local_version:
            lbl_text += " (Current)"

        lbl = ctk.CTkLabel(frame, text=lbl_text, font=ctk.CTkFont(size=13, weight="bold"))
        lbl.pack(side="left", anchor="w")

        action_btn = ctk.CTkButton(
            frame,
            text="Switch Version",
            width=110,
            command=lambda: self.start_version_switch(tag_name, zipball_url, action_btn)
        )

        if tag_name == self.parent_app.local_version:
            action_btn.configure(state="disabled", text="Installed", fg_color="#2E7D32")

        action_btn.pack(side="right")

    def start_version_switch(self, tag_name, zipball_url, btn):
        btn.configure(text="Installing...", state="disabled", fg_color="#EF6C00")
        threading.Thread(target=self.parent_app.install_version, args=(zipball_url, tag_name, self), daemon=True).start()


class PluginStoreWindow(ctk.CTkToplevel):
    def __init__(self, parent_app):
        super().__init__()
        self.parent_app = parent_app
        self.title("Jarvis Plugin Downloader")
        self.geometry("550x550")
        self.attributes("-topmost", True)

        title_lbl = ctk.CTkLabel(self, text="Browse & Install Plugins", font=ctk.CTkFont(size=16, weight="bold"))
        title_lbl.pack(pady=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=500, height=420)
        self.scroll_frame.pack(pady=10, fill="both", expand=True, padx=15)

        self.status_lbl = ctk.CTkLabel(self.scroll_frame, text="Fetching online repository directory...")
        self.status_lbl.pack(pady=20)

        threading.Thread(target=self.fetch_remote_plugins, daemon=True).start()

    def fetch_remote_plugins(self):
        repo_url = f"{REPO_URL}/contents/plugins"
        try:
            req = urllib.request.Request(repo_url, headers={'User-Agent': 'JarvisClient'})
            with urllib.request.urlopen(req) as response:
                files = json.loads(response.read().decode())

            self.status_lbl.destroy()
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

        local_path = os.path.join(jarvis_engine.PLUGINS_DIR, filename)
        is_installed = os.path.exists(local_path)

        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", pady=6, padx=5)

        display_name = filename.replace(".py", "").replace("_", " ").title()
        lbl = ctk.CTkLabel(frame, text=display_name, font=ctk.CTkFont(size=13, weight="bold"))
        lbl.pack(side="left", anchor="w")

        btn_container = ctk.CTkFrame(frame, fg_color="transparent")
        btn_container.pack(side="right", anchor="e")

        self.render_row_buttons(btn_container, filename, plugin_info, is_installed)

    def render_row_buttons(self, container_widget, filename, plugin_info, is_installed):
        for child in container_widget.winfo_children():
            child.destroy()

        action_btn = ctk.CTkButton(container_widget, width=90)

        if is_installed:
            action_btn.configure(text="Installed", state="disabled", fg_color="#2E7D32")
            uninstall_btn = ctk.CTkButton(
                container_widget,
                text="Uninstall",
                width=80,
                fg_color="#D32F2F",
                hover_color="#B71C1C",
                command=lambda: self.uninstall_plugin(filename, container_widget, plugin_info)
            )
            uninstall_btn.pack(side="right", padx=(5, 0))
        else:
            action_btn.configure(text="Install",
                                 command=lambda: self.start_download(filename, plugin_info["download_url"], action_btn,
                                                                     container_widget, plugin_info))

        action_btn.pack(side="right")

    def start_download(self, filename, url, button_widget, container_widget, plugin_info):
        button_widget.configure(text="Downloading...", state="disabled", fg_color="#EF6C00")
        threading.Thread(target=self.download_worker,
                         args=(filename, url, button_widget, container_widget, plugin_info), daemon=True).start()

    def download_worker(self, filename, url, button_widget, container_widget, plugin_info):
        try:
            os.makedirs(jarvis_engine.PLUGINS_DIR, exist_ok=True)
            local_path = os.path.join(jarvis_engine.PLUGINS_DIR, filename)

            req = urllib.request.Request(url, headers={'User-Agent': 'JarvisClient'})
            with urllib.request.urlopen(req) as response, open(local_path, 'wb') as out_file:
                out_file.write(response.read())

            self.parent_app.after(0, lambda: self.render_row_buttons(container_widget, filename, plugin_info,
                                                                     is_installed=True))
            jarvis_engine.load_plugins()
            self.parent_app.refresh_actions_on_toggle()

        except Exception as e:
            self.parent_app.after(0, lambda: button_widget.configure(text="Retry", state="normal", fg_color="#D32F2F"))

    def uninstall_plugin(self, filename, container_widget, plugin_info):
        local_path = os.path.join(jarvis_engine.PLUGINS_DIR, filename)
        try:
            if os.path.exists(local_path):
                os.remove(local_path)

            self.render_row_buttons(container_widget, filename, plugin_info, is_installed=False)
            jarvis_engine.load_plugins()
            self.parent_app.refresh_actions_on_toggle()

            if self.parent_app.settings_window and self.parent_app.settings_window.winfo_exists():
                self.parent_app.settings_window.clear_and_reload()
        except Exception as e:
            print(f"Failed to remove plugin file: {e}")


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

    def clear_and_reload(self):
        for child in self.scroll_frame.winfo_children():
            child.destroy()
        self.switches.clear()
        self.load_toggles()

    def load_toggles(self):
        jarvis_engine.load_plugins()

        for key, value in jarvis_engine.config.items():
            if key in ["none", "play_track", "next_track", "previous_track", "pause_track", "unpause_track",
                       "open_browser"]:
                continue

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
                "open_website": jarvis_engine.open_website,
                "question": jarvis_engine.question,
                "screenshot": jarvis_engine.take_screenshot,
                "online_question": jarvis_engine.google_question,
            }

            if key in CORE_MAPPING:
                jarvis_engine.ACTIONS[key] = CORE_MAPPING[key]
            else:
                jarvis_engine.load_plugins()

        self.parent_app.refresh_actions_on_toggle()


class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.local_version = self.get_local_version()
        self.title(f"JarvisMod {self.local_version}")
        self.geometry("800x570")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.settings_window = None
        self.store_window = None
        self.version_window = None
        self.latest_release_data = None

        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=15)

        self.title_lbl = ctk.CTkLabel(self.top_frame, text="JARVIS CONSOLE",
                                      font=ctk.CTkFont(size=18, weight="bold"))
        self.title_lbl.pack(side="left")

        self.btn_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.btn_frame.pack(side="right")

        # Auto-Update Button (Hidden/Grey initially)
        self.update_btn = ctk.CTkButton(self.btn_frame, text="Checking updates...", width=110, fg_color="gray", state="disabled", command=self.do_auto_update)
        self.update_btn.pack(side="left", padx=(0, 5))

        self.version_btn = ctk.CTkButton(self.btn_frame, text="🔄 Versions", width=90, command=self.open_version_manager)
        self.version_btn.pack(side="left", padx=(0, 5))

        self.store_btn = ctk.CTkButton(self.btn_frame, text="🔌 Plugin Store", width=110, command=self.open_store)
        self.store_btn.pack(side="left", padx=(0, 5))

        self.settings_btn = ctk.CTkButton(self.btn_frame, text="⚙ Settings", width=100, command=self.open_settings)
        self.settings_btn.pack(side="left")

        self.whisper_lbl = ctk.CTkLabel(self, text="Whisper Speech Transcript:", font=ctk.CTkFont(weight="bold"))
        self.whisper_lbl.pack(anchor="w", padx=20, pady=(5, 2))
        self.whisper_text = ctk.CTkTextbox(self, height=70, activate_scrollbars=True)
        self.whisper_text.pack(fill="x", padx=20)
        self.whisper_text.insert("0.0", "Awaiting wake word command entry...")

        self.jarvis_lbl = ctk.CTkLabel(self, text="Jarvis Framework Core Output:", font=ctk.CTkFont(weight="bold"))
        self.jarvis_lbl.pack(anchor="w", padx=20, pady=(15, 2))
        self.jarvis_text = ctk.CTkTextbox(self, height=130, activate_scrollbars=True)
        self.jarvis_text.pack(fill="x", padx=20)
        self.jarvis_text.insert("0.0", "Systems Idle.")

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

        self.status_lbl = ctk.CTkLabel(self, text="🟢 Wake Word Engine Active: Sleep Mode ('Hey Jarvis')",
                                       text_color="#4CAF50", font=ctk.CTkFont(weight="bold"))
        self.status_lbl.pack(pady=(0, 15))

        # Check for updates on startup
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def get_local_version(self):
        try:
            with open(VERSION_FILE, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "v1.3.0"

    def check_for_updates(self):
        try:
            req = urllib.request.Request(f"{REPO_URL}/releases/latest", headers={'User-Agent': 'JarvisClient'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

            latest_tag = data.get("tag_name")
            if latest_tag and latest_tag != self.local_version:
                self.latest_release_data = data
                self.after(0, lambda: self.update_btn.configure(
                    text=f"Update to {latest_tag}",
                    fg_color="#4CAF50",
                    hover_color="#388E3C",
                    state="normal"
                ))
            else:
                self.after(0, lambda: self.update_btn.configure(text="Up to date", state="disabled"))
        except Exception as e:
            self.after(0, lambda: self.update_btn.configure(text="Update check failed", state="disabled"))

    def do_auto_update(self):
        if self.latest_release_data:
            tag_name = self.latest_release_data.get("tag_name")
            zipball_url = self.latest_release_data.get("zipball_url")
            self.update_btn.configure(text="Downloading...", state="disabled", fg_color="#EF6C00")
            threading.Thread(target=self.install_version, args=(zipball_url, tag_name), daemon=True).start()

    def install_version(self, zip_url, tag_name, window_to_close=None):
        try:
            self.after(0, lambda: self.update_jarvis_ui(f"Downloading release payload for {tag_name}..."))
            req = urllib.request.Request(zip_url, headers={'User-Agent': 'JarvisClient'})
            with urllib.request.urlopen(req) as response:
                zip_data = response.read()

            self.after(0, lambda: self.update_jarvis_ui("Extracting files and applying update..."))
            with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                with tempfile.TemporaryDirectory() as tmpdir:
                    z.extractall(tmpdir)
                    extracted_folders = os.listdir(tmpdir)
                    if extracted_folders:
                        repo_root = os.path.join(tmpdir, extracted_folders[0])
                        # Overwrite files in the base directory
                        shutil.copytree(repo_root, BASE_DIR, dirs_exist_ok=True)

            # Manually update the version text to sync UI
            with open(VERSION_FILE, "w") as f:
                f.write(tag_name)

            success_msg = f"✅ Successfully installed {tag_name}!\n\nIMPORTANT: You must CLOSE this window and restart Jarvis for the engine updates to fully take effect."
            self.after(0, lambda: self.update_jarvis_ui(success_msg))
            self.after(0, lambda: self.update_btn.configure(text="Restart Required", fg_color="#2E7D32"))

            if window_to_close:
                self.after(0, window_to_close.destroy)

        except Exception as e:
            error_msg = f"Failed to install version: {e}"
            self.after(0, lambda: self.update_jarvis_ui(error_msg))
            self.after(0, lambda: self.update_btn.configure(text="Update Failed", fg_color="#D32F2F"))

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

    def open_version_manager(self):
        if self.version_window is None or not self.version_window.winfo_exists():
            self.version_window = VersionWindow(self)
        else:
            self.version_window.focus()

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