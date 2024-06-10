import RPi.GPIO as GPIO
import time
import subprocess
import json
import os
from dotenv import load_dotenv
import paho.mqtt.client as paho

# Load environment variables
load_dotenv()

# GPIO Pin Definitions (Physical pin numbers)
SWITCH_PIN = 12
BUTTON1_PIN = 18
BUTTON2_PIN = 22
BUTTON3_PIN = 13

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
GPIO.setmode(GPIO.BOARD)

def setup_gpio(pin, direction, pull_up_down=GPIO.PUD_DOWN):
    try:
        GPIO.setup(pin, direction, pull_up_down=pull_up_down)
        print(f"Successfully set up pin {pin}")
    except Exception as e:
        print(f"Error setting up pin {pin}: {e}")

# Initialize Playlists
load_playlists()

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

# MQTT Client Configuration
broker_address = os.environ.get('BROKER_ADDRESS')
broker_port = int(os.environ.get('BROKER_PORT'))
username = os.environ.get('USER_NAME')
password = os.environ.get('PASSWORD')

client = paho.Client()
client.username_pw_set(username, password)
try:
    client.connect(broker_address, broker_port)
except Exception as e:
    print(f"Error connecting to MQTT broker: {e}")
    exit(1)

# Play Song
def play_song(song_path):
    global current_script, is_playing
    stop_song()
    try:
        current_script = subprocess.Popen(['vlc', song_path])
        is_playing = True
    except Exception as e:
        print(f"Error playing song: {e}")

# Stop Song
def stop_song():
    global current_script, is_playing
    try:
        if current_script is not None:
            current_script.terminate()
            current_script = None
            is_playing = False
    except Exception as e:
        print(f"Error stopping song: {e}")

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

# Set up event detection with error handling
def add_event_detection(pin, edge, callback, bouncetime=300):
    try:
        GPIO.add_event_detect(pin, edge, callback=callback, bouncetime=bouncetime)
        print(f"Successfully added edge detection for pin {pin}")
    except RuntimeError as e:
        print(f"Error setting up GPIO event detection on pin {pin}: {e}")
        GPIO.cleanup()
        exit(1)
    except Exception as e:
        print(f"Unexpected error setting up GPIO event detection on pin {pin}: {e}")
        GPIO.cleanup()
        exit(1)

# Set up event detection for buttons and switch with longer bounce time (500 ms)
try:
    add_event_detection(BUTTON1_PIN, GPIO.RISING, button1_pressed, bouncetime=500)
    add_event_detection(BUTTON2_PIN, GPIO.RISING, button2_pressed, bouncetime=500)
    add_event_detection(BUTTON3_PIN, GPIO.RISING, button3_pressed, bouncetime=500)
    add_event_detection(SWITCH_PIN, GPIO.BOTH, switch_pressed, bouncetime=500)
except Exception as e:
    print(f"Error setting up event detection: {e}")
    GPIO.cleanup()
    exit(1)

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
