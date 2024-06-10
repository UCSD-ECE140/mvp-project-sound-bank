import os
import vlc
import paho.mqtt.client as paho
import RPi.GPIO as GPIO
from dotenv import load_dotenv

load_dotenv()

broker_address = os.getenv('BROKER_ADDRESS')
broker_port = int(os.getenv('BROKER_PORT'))
username = os.getenv('USER_NAME')
password = os.getenv('PASSWORD')

music_queue_list = []

# Initialize GPIO
GPIO.setmode(GPIO.BOARD)

def setup_gpio(pin, direction, pull_up_down=GPIO.PUD_DOWN):
    try:
        GPIO.setup(pin, direction, pull_up_down=pull_up_down)
        print(f"Successfully set up pin {pin}")
    except Exception as e:
        print(f"Error setting up pin {pin}: {e}")

# GPIO Pin Definitions (Physical pin numbers)
SWITCH_PIN = 12
BUTTON1_PIN = 18
BUTTON2_PIN = 22
BUTTON3_PIN = 13

# Initialize GPIO pins
try:
    setup_gpio(SWITCH_PIN, GPIO.IN)
    setup_gpio(BUTTON1_PIN, GPIO.IN)
    setup_gpio(BUTTON2_PIN, GPIO.IN)
    setup_gpio(BUTTON3_PIN, GPIO.IN)
except Exception as e:
    print(f"Error initializing GPIO pins: {e}")
    GPIO.cleanup()
    exit(1)

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
        self.print_queue_state()
        if not self.currently_playing:
            self.play_next()

    def play_next(self):
        if self.queue:
            if self.currently_playing is not None:
                self.currently_playing = None
            self.currently_playing = self.queue.pop(0)
            self.play_audio(self.currently_playing)
            self.print_queue_state()
        else:
            print("No songs")
            self.currently_playing = None
            self.print_queue_state()

    def play_audio(self, song):
        print(f"Now playing '{song}'.")
        self.player.set_media(vlc.Media(song))
        self.player.play()

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            print("Toggled: Playback Paused")
        else:
            self.player.play()
            print("Toggled: Playing Again")

    def skip(self):
        if self.player.is_playing():
            self.player.stop()
            print("Skipping current song...")
        self.play_next()

    def handle_end_of_song(self, event):
        print("Current song ended.")
        self.play_next()

    def print_queue_state(self):
        if self.queue:
            state_message = "Queue State:\n"
            state_message += f"Currently Playing: {self.currently_playing}\n"
            state_message += "Upcoming: " + ", ".join(self.queue)
            print(state_message)
        else:
            print("The queue is empty.")

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    if msg.topic == "queue/songs":
        song = msg.payload.decode("utf-8").strip()
        print(f"Received song request: {song}")
        music_queue.add_song(song)
    elif msg.topic == "queue/commands":
        command = msg.payload.decode("utf-8").strip().lower()
        print(f"Received command: {command}")
        if command == 'play':
            music_queue.toggle_play()
        elif command == 'skip':
            music_queue.skip()
        elif command == 'next':
            music_queue.play_next()

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
