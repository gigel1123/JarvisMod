import pyttsx3

def jarvis(response):
    talk = pyttsx3.init()
    talk.stop()
    talk.setProperty('rate', 175)
    talk.setProperty('volume', 1)
    talk.say(response)
    talk.runAndWait()