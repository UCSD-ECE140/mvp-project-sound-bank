import os
import vlc
import time
import paho.mqtt.client as paho
from dotenv import load_dotenv
from pytube import Search, YouTube

load_dotenv()

broker_address = os.getenv('BROKER_ADDRESS')
broker_port = int(os.getenv('BROKER_PORT'))
username = os.getenv('USER_NAME')
password = os.getenv('PASSWORD')
DOWNLOAD_PATH = r'C:\Users\mtyse\Documents\ece140\ECE140B\Tech2\mvp-project-sound-bank\soundbankfiles'

def get_first_audio_stream(song_query):
    try:
        s = Search(song_query)
        first_result = s.results[0].watch_url
        yt = YouTube(first_result)
        return yt.streams.filter(only_audio=True).first()
    except Exception as e:
        print(f"Error retrieving '{song_query}': {e}")
        return None

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def print_queue(self):
    if self.queue:
        print("Current Queue:")
        for song in self.queue:
            print(f" - {song}")
    else:
        print("The queue is empty.")

def on_message(client, userdata, msg):
    if msg.topic == "queue/songs":
        song_query = msg.payload.decode("utf-8").strip()
        print(f"Received song request: {song_query}")
        audio_stream = get_first_audio_stream(song_query)
        if audio_stream:
            music_queue.add_song(audio_stream.title)
        else:
            print(f"Failed to handle song request for '{song_query}'")
    elif msg.topic == "queue/commands":
        command = msg.payload.decode("utf-8").strip().lower()
        print(f"Received command: {command}")
        if command == 'play':
            music_queue.play_audio(music_queue.currently_playing)
            print(f"Playing: {music_queue.currently_playing}")
        elif command == 'toggle_play':
            music_queue.toggle_play()
        elif command == 'stop':
            music_queue.player.stop()
            print("Playback stopped")
        elif command == 'skip':
            music_queue.skip()

class MusicQueue:
    def __init__(self):
        self.queue = []
        self.currently_playing = None
        self.player = vlc.MediaPlayer()
        self.player_events = self.player.event_manager()
        self.player_events.event_attach(vlc.EventType.MediaPlayerEndReached, self.handle_end_of_song)
    def move_song(self, current_index, new_index):
        """Move a song in the queue from current_index to new_index."""
        if 0 <= current_index < len(self.queue) and 0 <= new_index < len(self.queue):
            song = self.queue.pop(current_index)
            self.queue.insert(new_index, song)
            print(f"Moved song from position {current_index} to {new_index}.")
        else:
            print("Invalid index.")
    def add_song(self, song):
        self.queue.append(song)
        print(f"Added '{song}' to the queue.")
        self.print_queue_state()
        if not self.currently_playing:
            self.play_next()

    def play_next(self):
        if self.queue:
            print("insplayself"+ self.queue[0])
            # Ensure the previous song file is deleted if it exists
            if self.currently_playing is not None :
                print(self.currently_playing)
                self.delete_song_file(self.currently_playing)
            self.currently_playing = self.queue.pop(0)
            print(self.currently_playing)
            self.download_and_play(self.currently_playing)
            self.print_queue_state()
        else:
            print("kakakak")
            self.currently_playing = None
            self.print_queue_state()

    def download_and_play(self, song):
        file_path = os.path.join(DOWNLOAD_PATH, song + '.mp4')
        if not os.path.exists(file_path):
            self.download_song(song)
        self.play_audio(song)

    def download_song(self, song):
        audio_stream = get_first_audio_stream(song)
        if audio_stream:
            audio_stream.download(output_path=DOWNLOAD_PATH, filename=song + '.mp4')
            print(f"Downloaded '{song}' to {DOWNLOAD_PATH}.")
        else:
            print(f"Failed to download '{song}'.")

    def play_audio(self, song):
        file_path = os.path.join(DOWNLOAD_PATH, song + '.mp4')
        self.player.set_media(vlc.Media(file_path))
        self.player.play()
        print(f"Now playing '{song}'.")

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            print("Toggled: Playback Paused")
        else:
            self.player.play()
            print("Toggled: Playing Again")

    def skip(self):
        print("skipping: " + self.currently_playing)
        if self.player.is_playing():
            self.player.stop()
            self.delete_song_file(self.currently_playing)
            print("Skipping current song...")
        self.play_next()

    def handle_end_of_song(self, event):
        print("Current song ended: W")
        self.play_next()

    def delete_song_file(self, song):
        file_path = os.path.join(DOWNLOAD_PATH, song + '.mp4')
        if os.path.exists(file_path):
            self.player.stop()  # Ensure VLC is not using the file
            retry_attempts = 3
            for attempt in range(retry_attempts):
                try:
                    os.remove(file_path)
                    print(f"Deleted '{file_path}'.")
                    break
                except PermissionError:
                    if attempt < retry_attempts - 1:  # Avoid sleeping on the last attempt
                        print(f"Unable to delete file on attempt {attempt + 1}. Retrying...")
                        time.sleep(1)  # Wait a bit before retrying
                    else:
                        print(f"Failed to delete file after {retry_attempts} attempts.")

    def print_queue_state(self):
        if self.currently_playing or self.queue:
            state_message = "Queue State:\n"
            if self.currently_playing:
                state_message += f"Currently Playing: {self.currently_playing}\n"
            if self.queue:
                state_message += "Upcoming: " + ", ".join(self.queue)
            else:
                state_message += "No upcoming songs."
            print(state_message)
        else:
            print("The queue is empty.")

music_queue = MusicQueue()

client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="uniqueid235", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)
client.username_pw_set(username, password=password)
client.connect(broker_address, broker_port)
client.on_subscribe = on_subscribe
client.on_message = on_message
client.subscribe("queue/#", qos=0)
client.loop_forever()
