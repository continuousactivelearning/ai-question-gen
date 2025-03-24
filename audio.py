import yt_dlp
import pickle
import os

# Function to get the base directory dynamically (works across devices)
def get_base_path():
    return os.path.dirname(os.path.realpath(__file__))

def download_audio(video_url):
    # Load cookies from the saved file
    cookies_file = os.path.join(get_base_path(), 'cookies.pkl')  # Update the path to match the location of the saved cookies
    with open(cookies_file, "rb") as f:
        cookies = pickle.load(f)

    # Dynamically determine the output path where the audio file will be saved
    audio_path = os.path.join(get_base_path(), 'audio.mp3')

    # yt-dlp options for downloading audio
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': audio_path,  # Path where you want to save the audio
        'cookies': cookies,  # Use cookies directly
    }

    # Download audio using yt-dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    return audio_path

# Prompt for video URL and call the function
video_url = input("Enter YouTube video URL: ")
file_path = download_audio(video_url)
print(f"Downloaded audio: {file_path}")
