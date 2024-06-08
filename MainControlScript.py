import RPi.GPIO as GPIO
import time
import threading
import subprocess
import json
import logging
import os
from dotenv import load_dotenv
import paho.mqtt.client as paho

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(filename='music_controller.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GPIO Pin Definitions
SWITCH_PIN = 17
BUTTON1_PIN = 27
BUTTON2_PIN = 22
BUTTON3_PIN = 23

# Global Variables
current_playlist_index = 0
current_song_index = 0
is_playing = False
playlists = []
current_script = None

# Load Playlists
def load_playlists():
    global playlists
    try:
        with open('playlists.json', 'r') as file:
            playlists = json.load(file)
        logging.info("Loaded playlists successfully.")
    except Exception as e:
        logging.error(f"Error loading playlists: {e}")

# Initialize GPIO
try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    logging.info("GPIO initialized successfully.")
except Exception as e:
    logging.error(f"Error initializing GPIO: {e}")

# Function to run a script
def run_script(script_name):
    global current_script
    if current_script:
        current_script.terminate()
    try:
        current_script = subprocess.Popen(['python', script_name])
        logging.info(f"Started script: {script_name}")
    except Exception as e:
        logging.error(f"Error starting script {script_name}: {e}")

# Functions for Button Actions
def iterate_playlists(channel):
    global current_playlist_index, current_song_index
    current_playlist_index = (current_playlist_index + 1) % len(playlists)
    current_song_index = 0
    print(f"Switched to playlist: {list(playlists.keys())[current_playlist_index]}")
    logging.info(f"Switched to playlist: {list(playlists.keys())[current_playlist_index]}")

def iterate_songs(channel):
    global current_song_index
    playlist_name = list(playlists.keys())[current_playlist_index]
    current_song_index = (current_song_index + 1) % len(playlists[playlist_name])
    print(f"Switched to song: {playlists[playlist_name][current_song_index]}")
    logging.info(f"Switched to song: {playlists[playlist_name][current_song_index]}")

def toggle_play_pause(channel):
    global is_playing
    is_playing = not is_playing
    command = 'resume' if is_playing else 'pause'
    print(f"Sending command: {command}")
    mqtt_client.publish("queue/commands", command)
    logging.info(f"Sent command: {command}")

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}: {msg.payload.decode('utf-8')}")
    logging.info(f"Received message on topic {msg.topic}: {msg.payload.decode('utf-8')}")

# MQTT Client Initialization
mqtt_client = paho.Client()
load_dotenv()

# broker_address = os.environ.get('BROKER_ADDRESS')
# broker_port = int(os.environ.get('BROKER_PORT'))
# username = os.environ.get('USER_NAME')
# password = os.environ.get('PASSWORD')

# client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="", userdata=None, protocol=paho.MQTTv5)


# GPIO Event Detection
try:
    GPIO.add_event_detect(BUTTON1_PIN, GPIO.FALLING, callback=iterate_playlists, bouncetime=300)
    GPIO.add_event_detect(BUTTON2_PIN, GPIO.FALLING, callback=iterate_songs, bouncetime=300)
    GPIO.add_event_detect(BUTTON3_PIN, GPIO.FALLING, callback=toggle_play_pause, bouncetime=300)
    logging.info("GPIO event detection setup successful.")
except Exception as e:
    logging.error(f"Error setting up GPIO event detection: {e}")

# Main Loop to monitor switch
try:
    load_playlists()
    while True:
        if GPIO.input(SWITCH_PIN) == GPIO.LOW:
            run_script('main.py')
        else:
            run_script('musicQueueRaspPi.py')
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    if current_script:
        current_script.terminate()
    GPIO.cleanup()
    logging.info("Music controller terminated.")
