# plugins/autoclicker_plugin.py
import time
import threading
from src import talk

PLUGIN_NAME = "auto_clicker"
PLUGIN_DESC = '"auto_clicker" (arguments: "level" [1-10], "duration" [seconds, or "infinity"]). Use this function when the user wants to start or activate the auto-clicker.'
KEYWORDS = ["activate auto clicker", "start auto clicker", "stop auto clicker", "stop clicker"]

CLICKER_ACTIVE = False

def click_worker(delay, duration):
    """Background thread optimized for extreme speed using pynput"""
    global CLICKER_ACTIVE
    from pynput.mouse import Button, Controller
    
    mouse = Controller()
    start_time = time.time()
    CLICKER_ACTIVE = True
    
    print(f"[AUTOCLICKER] Started with delay: {delay}s")
    
    # Cache the click function and Button object outside the loop for speed
    click_btn = Button.left
    
    if delay == 0.0:
        # ABSOLUTE MAX SPEED LOOP (Levels 9 & 10)
        # Removes all overhead and sleep functions
        if duration == "infinity":
            while CLICKER_ACTIVE:
                mouse.click(click_btn, 1)
        else:
            while CLICKER_ACTIVE and (time.time() - start_time) < duration:
                mouse.click(click_btn, 1)
    else:
        # REGULAR SPEED LOOP (Levels 1-8)
        while CLICKER_ACTIVE:
            if duration != "infinity" and (time.time() - start_time) > duration:
                break
            mouse.click(click_btn, 1)
            time.sleep(delay)
            
    CLICKER_ACTIVE = False
    print("[AUTOCLICKER] Stopped.")

def run(*args):
    global CLICKER_ACTIVE
    
    # Optimized delays for pynput
    levels = {
        1: 1.0,       # 1 click/sec
        2: 1/5,       # 5 clicks/sec
        3: 1/10,      # 10 clicks/sec
        4: 1/20,      # 20 clicks/sec
        5: 1/50,      # 50 clicks/sec
        6: 1/100,     # 100 clicks/sec
        7: 1/250,     # 250 clicks/sec
        8: 1/500,     # 500 clicks/sec
        9: 0.0,       # No delay (As fast as Python can go, usually ~500-1000 cps)
        10: 0.0       # Max raw power
    }

    user_speech = str(args).lower()
    
    if "stop" in user_speech or "disable" in user_speech or "turn off" in user_speech:
        if CLICKER_ACTIVE:
            CLICKER_ACTIVE = False
            talk.jarvis("Auto clicker has been stopped, sir.")
            return "Auto-clicker stopped successfully"
        else:
            talk.jarvis("The auto clicker is not currently running, sir.")
            return "Auto-clicker was not running"

    level = 1
    duration = 10 

    if args and isinstance(args[0], dict):
        ai_args = args[0]
        try:
            level = int(ai_args.get("level", 1))
            dur_val = ai_args.get("duration", 10)
            duration = "infinity" if str(dur_val).lower() in ["infinity", "infinite", "forever"] else int(dur_val)
        except:
            pass
    else:
        import re
        numbers = re.findall(r'\d+', user_speech)
        if len(numbers) >= 1:
            level = int(numbers[0])
        if len(numbers) >= 2:
            duration = int(numbers[1])
        if "infinity" in user_speech or "forever" in user_speech or "until" in user_speech:
            duration = "infinity"

    level = max(1, min(level, 10))
    delay = levels[level]

    if CLICKER_ACTIVE:
        CLICKER_ACTIVE = False
        time.sleep(0.1) 

    threading.Thread(target=click_worker, args=(delay, duration), daemon=True).start()
    
    time_phrase = "until you tell me to stop" if duration == "infinity" else f"for {duration} seconds"
    talk.jarvis(f"Activating auto clicker level {level}, {time_phrase}, sir.")
    
    return f"Auto-clicker level {level} started"

if __name__ == "__main__":
    run("1")