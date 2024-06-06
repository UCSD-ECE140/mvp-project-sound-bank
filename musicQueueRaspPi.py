import os
import vlc
import paho.mqtt.client as paho
from dotenv import load_dotenv
from pytube import Search, YouTube

load_dotenv()

broker_address = os.getenv('BROKER_ADDRESS')
broker_port = int(os.getenv('BROKER_PORT'))
username = os.getenv('USER_NAME')
password = os.getenv('PASSWORD')
DOWNLOAD_PATH = r'C:\\Users\\maxdg\\PycharmProjects\\ee140\\mvp-project-sound-bank'  # Use a raw string

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

def on_message(client, userdata, msg):
    if msg.topic == "queue/songs":
        song_query = msg.payload.decode("utf-8").strip()
        print(f"Received song request: {song_query}")
        audio_stream = get_first_audio_stream(song_query)
        if audio_stream:
            music_queue.add_song(audio_stream.title)
        else:
            print(f"Failed to handle song request for '{song_query}'")
    if msg.topic == "queue/commands":
        command = msg.payload.decode("utf-8").strip().lower()
        print(f"Received command: {command}")
        if command in ['play', 'pause', 'stop', 'skip']:
            music_queue.play_audio(music_queue.currently_playing, command)

class MusicQueue:
    def __init__(self):
        self.queue = []
        self.currently_playing = None
        self.player = vlc.MediaPlayer()
        self.player_events = self.player.event_manager()
        self.player_events.event_attach(vlc.EventType.MediaPlayerEndReached, self.handle_end_of_song)

    def add_song(self, song):
        self.queue.append(song)
        print(f"Added '{song}' to the queue.")
        if not self.currently_playing:
            self.play_next()

    def play_next(self):
        if self.queue:
            self.currently_playing = self.queue.pop(0)
            self.download_and_play(self.currently_playing)
        else:
            self.currently_playing = None
            print("The queue is empty.")

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

    def pause(self):
        if self.player.is_playing():
            self.player.pause()
            print("Playback paused")

    def skip(self):
        self.player.stop()
        print("Skipping current song...")
        self.play_next()

    def handle_end_of_song(self, event):
        print("Current song ended.")
        self.play_next()

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
