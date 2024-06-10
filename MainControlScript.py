import os
import vlc
import RPi.GPIO as GPIO
import json

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

# Initialize GPIO pins
try:
    setup_gpio(BUTTON1_PIN, GPIO.IN)
    setup_gpio(BUTTON2_PIN, GPIO.IN)
    setup_gpio(BUTTON3_PIN, GPIO.IN)
except Exception as e:
    print(f"Error initializing GPIO pins: {e}")
    GPIO.cleanup()
    exit(1)

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
    while player.is_playing():
        pass
    player.stop()

# Load the playlist from JSON
with open('playlists.json') as f:
    playlist = json.load(f)

# Function to handle button press events
def button_pressed(pin):
    if pin == BUTTON1_PIN:
        selected_genre = input("Enter the genre you want to play (or 'q' to quit): ")
        if selected_genre.lower() != 'q':
            play_genre(playlist, selected_genre)
    elif pin == BUTTON2_PIN:
        pass  # Implement functionality for button 2 if needed
    elif pin == BUTTON3_PIN:
        pass  # Implement functionality for button 3 if needed

# Add event detection for button presses
GPIO.add_event_detect(BUTTON1_PIN, GPIO.RISING, callback=lambda _: button_pressed(BUTTON1_PIN), bouncetime=300)
GPIO.add_event_detect(BUTTON2_PIN, GPIO.RISING, callback=lambda _: button_pressed(BUTTON2_PIN), bouncetime=300)
GPIO.add_event_detect(BUTTON3_PIN, GPIO.RISING, callback=lambda _: button_pressed(BUTTON3_PIN), bouncetime=300)

# Main loop
try:
    while True:
        pass  # Keep the program running
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
