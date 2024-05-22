import os
import json
from pytube import Search, YouTube

# Path to the directory containing the songs
songs_directory = r'C:\Users\Nehemiah Skandera\Desktop\ECE140B\Spotipy\mvp-project-sound-bank\SoundBankFiles'
# Path to the playlists file
playlists_file = 'playlists.json'

# Load existing playlists from the JSON file
def load_playlists(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

# Save playlists to the JSON file
def save_playlists(playlists, file_path):
    with open(file_path, 'w') as file:
        json.dump(playlists, file, indent=4)

# Function to add a song to a playlist
def add_song_to_playlist(playlist_name, song_path):
    playlists = load_playlists(playlists_file)
    if playlist_name not in playlists:
        playlists[playlist_name] = []
    if song_path not in playlists[playlist_name]:
        playlists[playlist_name].append(song_path)
        save_playlists(playlists, playlists_file)

# Function to download a song from YouTube
def download_song(song_query):
    s = Search(song_query)
    first_result = s.results[0].watch_url

    yt = YouTube(first_result)
    audio_stream = yt.streams.filter(only_audio=True).first()
    if audio_stream:
        song_path = os.path.join(songs_directory, song_query + ".mp4")
        audio_stream.download(output_path=songs_directory, filename=song_query + ".mp4")
        return song_path
    return None

# Function to handle instruction strings
def handle_instruction(instruction):
    try:
        playlist_name, song_title = instruction.split('", "')
        playlist_name = playlist_name.strip('"')
        song_title = song_title.strip('"')
        song_path = os.path.join(songs_directory, song_title + ".mp4")
        
        if not os.path.exists(song_path):
            print(f"Song '{song_title}' not found locally. Downloading...")
            song_path = download_song(song_title)
        
        if song_path:
            add_song_to_playlist(playlist_name, song_path)
        else:
            print(f"Failed to download song '{song_title}'.")
    except ValueError:
        print("Invalid instruction format. Use '\"PlaylistName\", \"SongTitle\"'.")

# Example usage: Add song to playlist based on instruction string
if __name__ == "__main__":
    instruction = '"Classic", "Emanuel Andrea Bocelli"'
    handle_instruction(instruction)
