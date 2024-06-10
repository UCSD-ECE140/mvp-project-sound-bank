import RPi.GPIO as GPIO
import time
import os
import vlc
import paho.mqtt.client as paho
from dotenv import load_dotenv
from pytube import Search, YouTube

load_dotenv()

# Load environment variables
broker_address = os.getenv('BROKER_ADDRESS')
broker_port = int(os.getenv('BROKER_PORT'))
username = os.getenv('USER_NAME')
password = os.getenv('PASSWORD')
DOWNLOAD_PATH = r'SoundBankFiles'

# GPIO Pin Definitions (Physical pin numbers)
PAUSE_PLAY_PIN = 18
NEXT_SONG_PIN = 22
NEXT_PLAYLIST_PIN = 13

# Initialize GPIO
GPIO.setmode(GPIO.BOARD)

def setup_gpio(pin, direction, pull_up_down=GPIO.PUD_DOWN):
    try:
        GPIO.setup(pin, direction, pull_up_down=pull_up_down)
        print(f"Successfully set up pin {pin}")
    except Exception as e:
        print(f"Error setting up pin {pin}: {e}")

# Initialize GPIO pins
try:
    setup_gpio(PAUSE_PLAY_PIN, GPIO.IN)
    setup_gpio(NEXT_SONG_PIN, GPIO.IN)
    setup_gpio(NEXT_PLAYLIST_PIN, GPIO.IN)
except Exception as e:
    print(f"Error initializing GPIO pins: {e}")
    GPIO.cleanup()
    exit(1)

# MQTT Client Configuration
client = paho.Client()
client.username_pw_set(username, password=password)
client.connect(broker_address, broker_port)

music_queue_list = []

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

def on_message(client, userdata, msg):
    if msg.topic == "queue/songs":
        song_query = msg.payload.decode("utf-8").strip()
        print(f"Received song request: {song_query}")
        
        audio_stream = get_first_audio_stream(song_query)
        if audio_stream:
            music_queue.add_song(audio_stream.title)
            music_queue_list.append(song_query)
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
            music_queue.stop()
            print("Playback stopped")
        elif command == 'skip':
            music_queue.skip()
        elif command == 'next':
            music_queue.play_next()
        elif command == 'test':
            broadcast_queue_state()

class MusicQueue:
    def __init__(self):
        self.queue = []
        self.currently_playing = None
        self.last_song = None
        self.player = vlc.MediaPlayer()
        self.player_events = self.player.event_manager()
        self.player_events.event_attach(vlc.EventType.MediaPlayerEndReached, self.handle_end_of_song)

    def add_song(self, song):
        self.queue.append(song)
        print(f"Added '{song}' to the queue.")
        self.download_song(song)
        self.print_queue_state()
        if not self.currently_playing:
            self.play_next()

    def play_next(self):
        if self.queue:
            if self.currently_playing is not None :
                self.delete_song_file(self.currently_playing)
            self.currently_playing = self.queue.pop(0)
            self.play_audio(self.currently_playing)
            self.last_song = self.currently_playing
            self.print_queue_state()
        else:
            print("No songs")
            self.currently_playing = None
            self.print_queue_state()

    def download_and_play(self, song):
        file_path = os.path.join(DOWNLOAD_PATH, song + '.mp4')
        if not os.path.exists(file_path):
            self.download_song(song)
        self.play_audio(song)
        self.last_song = self.currently_playing

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

    def stop(self):
        if self.player.is_playing():
            self.player.stop()
            self.delete_song_file(self.currently_playing)

    def skip(self):
        if self.player.is_playing():
            self.player.stop()
            self.delete_song_file(self.currently_playing)
        self.play_next()

    def handle_end_of_song(self, event):
        self.play_next_end()

    def play_next_end(self):
        self.delete_song_file(self.last_song)
        self.currently_playing = self.queue.pop(0)
        self.play_audio(self.currently_playing)

    def delete_song_file(self, song):
        file_path = os.path.join(DOWNLOAD_PATH, song + '.mp4')
        if os.path.exists(file_path):
            retry_attempts = 3
            for attempt in range(retry_attempts):
                try:
                    os.remove(file_path)
                    print(f"Deleted '{file_path}'.")
                    music_queue_list.pop()
                    break
                except PermissionError:
                    if attempt < retry_attempts - 1:
                        print(f"Unable to delete file on attempt {attempt + 1}. Retrying...")
                        time.sleep(1)
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

        client.publish("queue/state", state_message, qos=0)

def broadcast_queue_state():
    for i in music_queue_list:
        print(i)

music_queue = MusicQueue()

client.on_connect = on_connect
client.username_pw_set(username, password=password)
client.connect(broker_address, broker_port)
