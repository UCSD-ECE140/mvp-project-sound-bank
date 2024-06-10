import os
import vlc
import RPi.GPIO as GPIO
import json
import time

# GPIO Pin Definitions (Physical pin numbers)
BUTTON1_PIN = 18
BUTTON2_PIN = 22
BUTTON3_PIN = 13

# Initialize GPIO
GPIO.setmode(GPIO.BOARD)

def setup_gpio(pin, direction, pull_up_down=GPIO.PUD_DOWN):
    try:
        GPIO.setup(pin, direction, pull_up_down=pull_up_down)
        print(f"Successfully set up pin {pin}")
    except Exception as e:
        print(f"Error setting up pin {pin}: {e}")

# Load the playlist from JSON
with open('playlists.json') as f:
    playlists = json.load(f)

# Initialize GPIO pins
try:
    setup_gpio(BUTTON1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    setup_gpio(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    setup_gpio(BUTTON3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
except Exception as e:
    print(f"Error initializing GPIO pins: {e}")
    GPIO.cleanup()
    exit(1)

# Function to play an audio file using VLC
def play_audio(file_path):
    print(f"Playing {file_path}")
    player = vlc.MediaPlayer(file_path)
    player.play()
    # Wait for the song to finish playing
    while player.get_state() != vlc.State.Ended:
        pass
    player.stop()

# Function to handle button press events
def check_button_press():
    global current_playlist_index, current_song_index, is_playing
    
    # Button 1: Iterate through playlists
    if not GPIO.input(BUTTON1_PIN):
        current_playlist_index = (current_playlist_index + 1) % len(playlists)
        print("Switched to Playlist:", list(playlists.keys())[current_playlist_index])
        time.sleep(0.5)  # Debounce delay
    
    # Button 2: Iterate through songs within playlist
    elif not GPIO.input(BUTTON2_PIN):
        current_playlist = list(playlists.keys())[current_playlist_index]
        current_song_index = (current_song_index + 1) % len(playlists[current_playlist])
        print("Switched to Song:", playlists[current_playlist][current_song_index])
        time.sleep(0.5)  # Debounce delay
    
    # Button 3: Pause or Play current song
    elif not GPIO.input(BUTTON3_PIN):
        if is_playing:
            print("Paused")
            is_playing = False
            # Pause current song
            # Implement pause functionality here
        else:
            print("Playing")
            is_playing = True
            # Resume playing current song
            # Implement play functionality here

# Initialize global variables
current_playlist_index = 0
current_song_index = 0
is_playing = False

# Main loop
try:
    while True:
        check_button_press()
        time.sleep(0.1)  # Small delay to reduce CPU usage
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
