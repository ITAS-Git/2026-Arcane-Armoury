"""
Arcane Armory – Physical Button HP Control

This script runs on the Raspberry Pi and listens for physical
button presses connected to GPIO pins.

When a button is pressed:
- It sends a POST request to the Flask backend
- The backend updates the character's HP in the database
- The player screen updates in real time

Author: Alexander Preston
Course: ITAS 164
"""

import RPi.GPIO as GPIO     # Library for controlling Raspberry Pi GPIO pins
import time                 # Used for debounce timing
import requests             # Used to send HTTP requests to Flask API


# ---------------------------------------------------
# CONFIGURATION SECTION
# ---------------------------------------------------

# BCM pin numbering is used (recommended standard)
# These are the GPIO pins connected to the buttons

HP_UP_PIN = 17      # GPIO pin for increasing HP
HP_DOWN_PIN = 27    # GPIO pin for decreasing HP

# Character ID being controlled
# In future versions, this could change dynamically
CHARACTER_ID = 1

# Flask API endpoint that handles HP updates
API_URL = "http://localhost:5000/api/update_hp"

# Software debounce delay (in seconds)
# Prevents multiple triggers from one physical press
DEBOUNCE_TIME = 0.2


# ---------------------------------------------------
# GPIO INITIALIZATION
# ---------------------------------------------------

# Set GPIO mode to BCM (Broadcom chip numbering)
GPIO.setmode(GPIO.BCM)

# Disable warnings (optional but keeps terminal clean)
GPIO.setwarnings(False)

# Configure pins as input with internal pull-up resistors
# Pull-up means:
# - Default state = HIGH
# - Button press connects pin to GND → LOW
GPIO.setup(HP_UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(HP_DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# Track last button press time for debounce control
last_press_time = 0


# ---------------------------------------------------
# FUNCTION: Send HP Update to Flask
# ---------------------------------------------------

def update_hp(amount):
    """
    Sends a POST request to the Flask backend API
    with the HP change amount (+1 or -1).

    The Flask server will:
    - Validate the value
    - Update the database
    - Return confirmation
    """
    try:
        payload = {
            "character_id": CHARACTER_ID,
            "delta": amount
        }

        # Send POST request to Flask server
        response = requests.post(API_URL, json=payload)

        # Basic response validation
        if response.status_code == 200:
            print(f"HP updated by {amount}")
        else:
            print("API error:", response.text)

    except Exception as e:
        # Handles server offline / network errors
        print("Connection error:", e)


# ---------------------------------------------------
# BUTTON CALLBACK FUNCTIONS
# ---------------------------------------------------

def handle_hp_up(channel):
    """
    Triggered when the HP increase button is pressed.
    Uses debounce logic to prevent rapid double-triggering.
    """
    global last_press_time

    current_time = time.time()

    # Check if enough time has passed since last press
    if current_time - last_press_time > DEBOUNCE_TIME:
        update_hp(+1)
        last_press_time = current_time


def handle_hp_down(channel):
    """
    Triggered when the HP decrease button is pressed.
    Also uses debounce protection.
    """
    global last_press_time

    current_time = time.time()

    if current_time - last_press_time > DEBOUNCE_TIME:
        update_hp(-1)
        last_press_time = current_time


# ---------------------------------------------------
# EVENT DETECTION (INTERRUPT-BASED INPUT)
# ---------------------------------------------------

"""
Instead of constantly checking button state (polling),
we use interrupt-based detection.

GPIO.FALLING means:
- Trigger when signal changes from HIGH to LOW
- This happens when button is pressed (because pull-up resistor is used)

bouncetime=200 adds additional hardware-level debounce (milliseconds).
"""

GPIO.add_event_detect(
    HP_UP_PIN,
    GPIO.FALLING,
    callback=handle_hp_up,
    bouncetime=200
)

GPIO.add_event_detect(
    HP_DOWN_PIN,
    GPIO.FALLING,
    callback=handle_hp_down,
    bouncetime=200
)


print("HP Button System Active")


# ---------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------

"""
The script must remain running so that
GPIO event detection continues to function.

If the program exits, button detection stops.
"""

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    # Allows safe shutdown with Ctrl+C
    print("Shutting down GPIO...")
    GPIO.cleanup()   # Resets GPIO pins to safe state