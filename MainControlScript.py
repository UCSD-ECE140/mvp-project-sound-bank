import RPi.GPIO as GPIO
import time
import subprocess
import json
import os
from dotenv import load_dotenv
import paho.mqtt.client as paho

# Load environment variables
load_dotenv()

# GPIO Pin Definitions
SWITCH_PIN = 12
BUTTON1_PIN = 27
BUTTON2_PIN = 22
BUTTON3_PIN = 23

# Global Variables
current_playlist_index = 0
current_song_index = 0
is_playing = False
playlists = []
current_script = None
queue = []
use_queue = False

# Load Playlists
def load_playlists():
    global playlists
    try:
        with open('playlists.json', 'r') as file:
            playlists = json.load(file)
    except Exception as e:
        print(f"Error loading playlists: {e}")

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUTTON1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUTTON3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Initialize Playlists
load_playlists()

# MQTT Client Configuration
broker_address = os.environ.get('BROKER_ADDRESS')
broker_port = int(os.environ.get('BROKER_PORT'))
username = os.environ.get('USER_NAME')
password = os.environ.get('PASSWORD')

client = paho.Client()
client.username_pw_set(username, password)
client.connect(broker_address, broker_port)

# Play Song
def play_song(song_path):
    global current_script, is_playing
    stop_song()
    current_script = subprocess.Popen(['vlc', song_path])
    is_playing = True

# Stop Song
def stop_song():
    global current_script, is_playing
    if current_script is not None:
        current_script.terminate()
        current_script = None
        is_playing = False

# Button Handlers
def button1_pressed(channel):
    global current_playlist_index, current_song_index
    if not use_queue:
        current_playlist_index = (current_playlist_index + 1) % len(playlists)
        current_song_index = 0
        play_current_song()

def button2_pressed(channel):
    global current_song_index
    if not use_queue:
        current_song_index = (current_song_index + 1) % len(playlists[current_playlist_name()])
        play_current_song()

def button3_pressed(channel):
    global is_playing
    if is_playing:
        stop_song()
    else:
        play_current_song()

def switch_pressed(channel):
    global use_queue
    use_queue = GPIO.input(SWITCH_PIN) == GPIO.HIGH
    if use_queue and queue:
        play_song(queue[0])
    elif not use_queue:
        play_current_song()

# Get Current Playlist Name
def current_playlist_name():
    return list(playlists.keys())[current_playlist_index]

# Play Current Song
def play_current_song():
    stop_song()
    playlist_name = current_playlist_name()
    if playlist_name in playlists and playlists[playlist_name]:
        song_path = playlists[playlist_name][current_song_index]
        play_song(song_path)

# MQTT on_message Callback
def on_message(client, userdata, message):
    global queue
    try:
        song_path = message.payload.decode('utf-8')
        queue.append(song_path)
        if use_queue and not is_playing:
            play_song(song_path)
    except Exception as e:
        print(f"Error handling MQTT message: {e}")

# Set up event detection
GPIO.add_event_detect(BUTTON1_PIN, GPIO.RISING, callback=button1_pressed, bouncetime=300)
GPIO.add_event_detect(BUTTON2_PIN, GPIO.RISING, callback=button2_pressed, bouncetime=300)
GPIO.add_event_detect(BUTTON3_PIN, GPIO.RISING, callback=button3_pressed, bouncetime=300)
GPIO.add_event_detect(SWITCH_PIN, GPIO.BOTH, callback=switch_pressed, bouncetime=300)

# MQTT Configuration
client.on_message = on_message
client.subscribe("queue/add")
client.loop_start()

# Main Loop
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
    client.loop_stop()
    stop_song()
