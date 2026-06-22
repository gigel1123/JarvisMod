# plugins/test_plugin.py

# 1. The action name Jarvis and Llama 3 will use in the JSON payload
PLUGIN_NAME = "test_print"

# 2. The instruction injected into the AI's system prompt telling it when to use this
PLUGIN_DESC = '"test_print" (no arguments. Use this function when the user explicitly asks to run a test or check if plugins are working)'

# 3. BYPASS KEYWORDS (Optional): Define 1-3 keywords to completely bypass the AI.
# If any of these are spoken, Jarvis runs this file immediately.
KEYWORDS = ["run test", "test plugin", "test"]


# 4. The actual function Jarvis executes when the action matches.
# Using *args makes sure it won't crash when receiving arguments from either the AI or a keyword bypass.
def run(*args):
    import talk

    # Print to your console terminal
    print("\n[PLUGIN SUCCESS] The dynamic drop-in test plugin was called successfully!")

    # Make Jarvis speak to confirm it works
    talk.jarvis("The test plugin executed successfully, sir! Everything is working perfectly.")

    return "test plugin executed successfully"