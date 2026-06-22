import os
import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model
import jarvis
import talk

# Callback hooks to pass string statuses back into GUI console easily
on_status_msg_change = None


def run_wake_word_engine():
    # Automatically download models if they are missing
    openwakeword.utils.download_models()

    # 1. Initialize openWakeWord with the exact model name 'hey_jarvis'
    model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")

    # 2. Setup PyAudio microphone stream
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1280  # openWakeWord expects 80 ms chunks at 16kHz

    audio = pyaudio.PyAudio()

    mic_stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print("🤖 Jarvis is in sleep mode. Say 'Hey Jarvis' to wake me up...")
    talk.jarvis("JARVIS INITIALIZED")

    def trigger_jarvis():
        print("\n🔊 Listening for your command...")
        if on_status_msg_change:
            on_status_msg_change("🔊 Wake Word Triggered! Listening to your voice...", "#FFCC00")

        talk.jarvis("Yes sir?")
        jarvis.get_voice_command()

        print("\n💤 Going back to sleep. Listening for wake word...\n")
        if on_status_msg_change:
            on_status_msg_change("🟢 Wake Word Engine Active: Sleep Mode ('Hey Jarvis')", "#4CAF50")

    # 3. Main background listening loop
    try:
        while True:
            # Read audio data from the mic
            audio_data = mic_stream.read(CHUNK, exception_on_overflow=False)

            # Convert audio buffer to a numpy array expected by the model
            audio_frame = np.frombuffer(audio_data, dtype=np.int16)

            # Cast to float64 for volume checking to prevent the math warning/overflow
            audio_frame_float = audio_frame.astype(np.float64)
            rms = np.sqrt(np.mean(audio_frame_float ** 2))

            # Feed the frame to openWakeWord
            prediction = model.predict(audio_frame)

            # Check the confidence score for "hey_jarvis"
            jarvis_score = prediction.get("hey_jarvis", 0)

            # REAL-TIME MONITOR (Shows mic activity and confidence score)
            print(f"🎤 Mic Volume: {rms:<5.1f} | 🧠 Jarvis Score: {jarvis_score:.4f}", end="\r")

            # Check if the confidence score is high enough.
            if jarvis_score > 0.45:
                print(f"\n\n⚡ Wake word detected! (Confidence: {jarvis_score:.2f})")

                # Pause the wake-word mic stream so it doesn't conflict with Whisper
                mic_stream.stop_stream()

                # CRITICAL: Reset the openWakeWord memory buffer completely!
                model.reset()

                # Run your main voice assistant logic
                trigger_jarvis()

                # Clear out any leftover junk audio that accumulated
                mic_stream.fl_discard = True if hasattr(mic_stream, 'fl_discard') else None

                # Restart the mic stream to listen for the next wake word
                mic_stream.start_stream()

    except Exception as e:
        print(f"Error inside wake word tracking array: {e}")
    finally:
        print("\nShutting down safely...")
        mic_stream.stop_stream()
        mic_stream.close()
        audio.terminate()