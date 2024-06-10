import RPi.GPIO as GPIO
import json

# GPIO Pin Definitions (Physical pin numbers)
BUTTON1_PIN = 18
BUTTON2_PIN = 22
BUTTON3_PIN = 13

# Load the playlist from JSON
with open('playlists.json') as f:
    playlist = json.load(f)

# Initialize GPIO
GPIO.setmode(GPIO.BOARD)

def setup_gpio(pin, direction, pull_up_down=GPIO.PUD_DOWN):
    try:
        GPIO.setup(pin, direction, pull_up_down=pull_up_down)
        print(f"Successfully set up pin {pin}")
    except Exception as e:
        print(f"Error setting up pin {pin}: {e}")

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
def add_event_detection(pin, callback):
    try:
        GPIO.add_event_detect(pin, GPIO.RISING, callback=callback, bouncetime=300)
        print(f"Successfully added edge detection for pin {pin}")
    except RuntimeError as e:
        print(f"Error setting up GPIO event detection on pin {pin}: {e}")
        GPIO.cleanup()
        exit(1)

# Initialize GPIO pins
try:
    setup_gpio(BUTTON1_PIN, GPIO.IN)
    setup_gpio(BUTTON2_PIN, GPIO.IN)
    setup_gpio(BUTTON3_PIN, GPIO.IN)
except Exception as e:
    print(f"Error initializing GPIO pins: {e}")
    GPIO.cleanup()
    exit(1)

# Set up event detection for buttons
add_event_detection(BUTTON1_PIN, lambda _: button_pressed(BUTTON1_PIN))
add_event_detection(BUTTON2_PIN, lambda _: button_pressed(BUTTON2_PIN))
add_event_detection(BUTTON3_PIN, lambda _: button_pressed(BUTTON3_PIN))

# Main loop
try:
    while True:
        pass  # Keep the program running
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
