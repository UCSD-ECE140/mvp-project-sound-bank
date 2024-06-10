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

# Function to play songs from a playlist for a specified genre
def play_genre(playlist, genre):
    if genre in playlist:
        print("Genre:", genre)
        for song_path in playlist[genre]:
            play_audio(song_path)
    else:
        print(f"Genre '{genre}' does not exist in the playlist.")

# Function to play an audio file using VLC
def play_audio(file_path):
    print(f"Playing {file_path}")
    player = vlc.MediaPlayer(file_path)
    player.play()
    # Wait for the song to finish playing
    while player.get_state() != vlc.State.Ended:
        pass
    player.stop()

# Load the playlist from JSON
with open('playlists.json') as f:
    playlist = json.load(f)

# Initialize GPIO pins
try:
    setup_gpio(BUTTON1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    setup_gpio(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    setup_gpio(BUTTON3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
except Exception as e:
    print(f"Error initializing GPIO pins: {e}")
    GPIO.cleanup()
    exit(1)

# Function to handle button press events
def check_button_press():
    if not GPIO.input(BUTTON1_PIN):
        selected_genre = input("Enter the genre you want to play (or 'q' to quit): ")
        if selected_genre.lower() != 'q':
            play_genre(playlist, selected_genre)
    elif not GPIO.input(BUTTON2_PIN):
        pass  # Implement functionality for button 2 if needed
    elif not GPIO.input(BUTTON3_PIN):
        pass  # Implement functionality for button 3 if needed

# Main loop
try:
    while True:
        check_button_press()
        time.sleep(0.1)  # Small delay to reduce CPU usage
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
