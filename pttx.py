import pyttsx3

# Initialize the TTS engine
engine = pyttsx3.init()

# Set properties (optional)
engine.setProperty("rate", 150)  # Speed of speech
engine.setProperty("volume", 0.9)  # Volume (0.0 to 1.0)

# Get available voices and set a specific voice
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)  # Choose a voice (e.g., male or female)

# Text to be converted to speech
text = """Music is the arrangement of sounds to create harmony, rhythm, and melody. It is a universal form of expression that connects people across cultures."""

# Convert text to speech
engine.say(text)

# Wait for the speech to finish
engine.runAndWait()

# Save the output to an audio file (if supported by the platform)
engine.save_to_file(text, "output_audio.mp3")
engine.runAndWait()
