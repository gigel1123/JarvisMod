import threading
import time
import tkinter as tk
import winsound
from win10toast import ToastNotifier

# These variables tell Jarvis's LLM reasoning engine what this plugin does
PLUGIN_NAME = "desktop_timer"
PLUGIN_DESC = '"desktop_timer" (arguments: duration_in_seconds, reminder_message) - When asked to remind of something after some amount of time like a reminder/timer please use this function.'


class FloatingTimerWidget:
    def __init__(self, seconds, message):
        self.seconds_left = seconds
        self.message = message

        # Create floating frameless window
        self.root = tk.Tk()
        self.root.title("Jarvis Timer")
        self.root.geometry("250x80+30+30")  # Size and position on screen (top-left)
        self.root.overrideredirect(True)  # Removes window borders/title bar
        self.root.attributes("-topmost", True)  # Forces window to stay on top
        self.root.configure(bg="#1E1E24")

        # Make it draggable by clicking anywhere on the background
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.stop_drag)

        # UI Layout
        self.time_lbl = tk.Label(
            self.root,
            text=self.format_time(self.seconds_left),
            font=("Consolas", 22, "bold"),
            fg="#4CAF50",
            bg="#1E1E24"
        )
        self.time_lbl.pack(pady=(8, 2))

        # Truncate long messages so they look clean in the widget
        display_msg = message if len(message) <= 25 else message[:22] + "..."
        self.msg_lbl = tk.Label(
            self.root,
            text=display_msg,
            font=("Segoe UI", 9, "italic"),
            fg="#AAAAAA",
            bg="#1E1E24"
        )
        self.msg_lbl.pack()

        # Start countdown tracking loops
        self.update_countdown()
        self.root.mainloop()

    def format_time(self, total_seconds):
        mins, secs = divmod(total_seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    def update_countdown(self):
        if self.seconds_left > 0:
            self.seconds_left -= 1
            self.time_lbl.configure(text=self.format_time(self.seconds_left))

            # Flash red when less than 10 seconds remain
            if self.seconds_left <= 10:
                self.time_lbl.configure(fg="#FF5252")

            self.root.after(1000, self.update_countdown)
        else:
            # When time runs out, trigger alarm on a background thread and close window
            threading.Thread(target=self.play_alarm, daemon=True).start()
            self.root.destroy()

    def play_alarm(self):
        """Triggers native Windows push notification and plays an audible beep loop."""
        try:
            toaster = ToastNotifier()
            toaster.show_toast(
                "Jarvis Alert",
                self.message,
                duration=5,
                threaded=True
            )
        except Exception:
            pass

        # Ringing pattern: 3 rapid succession high-pitched tones
        for _ in range(3):
            winsound.Beep(2500, 400)  # Frequency: 2500Hz, Duration: 400ms
            time.sleep(0.1)

    # Draggable logic handlers
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def stop_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")


def run(duration_in_seconds, reminder_message="Time is up!"):
    """Main execution path triggered by Jarvis."""
    try:
        seconds = int(duration_in_seconds)
    except ValueError:
        print(f"Error: Invalid timer duration received: {duration_in_seconds}")
        return

    print(f"⏰ UI Timer initialized for {seconds} seconds: {reminder_message}")

    # Run the GUI window instantiation inside a standalone background thread
    # This prevents the primary UI/Audio threads inside Jarvis from hanging
    gui_thread = threading.Thread(target=FloatingTimerWidget, args=(seconds, reminder_message))
    gui_thread.daemon = True
    gui_thread.start()
run(10, "time")