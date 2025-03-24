import os

# Check the files in the current directory (or any other directory you're working with)
print("Files in current directory:", os.listdir("."))

# Fix the file name if needed
old_path = "audio.mp3.mp3"  # Update this to your file's path
new_path = "audio.mp3"

if os.path.exists(old_path):
    os.rename(old_path, new_path)
    print(f"Renamed: {old_path} → {new_path}")
else:
    print("Audio file not found!")

import IPython.display as ipd

# Set the correct file path
audio_path = "C:/Users/Family/OneDrive/Desktop/cookies_automate/audio.mp3"  # Update this to your file's path

# Play the audio with the correct sample rate (e.g., 44100 Hz)
ipd.Audio(audio_path, rate=44100)
