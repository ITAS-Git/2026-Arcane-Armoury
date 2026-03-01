"""
Arcane Armory – Bluetooth Button HP Control (BLE)

Listens for BLE notifications from an ESP32 and forwards
HP delta updates to the Flask backend.

ESP32 payload format (examples):
  P1:+1
  P1:-1

Author: Alexander Preston
Course: ITAS 164
"""

import asyncio
import requests
from bleak import BleakClient, BleakScanner

# ---------------------------
# CONFIG
# ---------------------------

# Flask API endpoint that updates HP
API_URL = "http://localhost:5000/api/update_hp"

# Map ESP32 "player key" to database character_id
PLAYER_TO_CHARACTER_ID = {
    "P1": 1,
    "P2": 2,
    "P3": 3,
    "P4": 4,
}

# Match these UUIDs to your ESP32 BLE Service/Characteristic
SERVICE_UUID = "8f3a2f10-6c5f-4c3d-a9a0-111111111111"
CHAR_EVENT_UUID = "8f3a2f11-6c5f-4c3d-a9a0-222222222222"

# If you know the ESP32 name, set it here (recommended)
TARGET_DEVICE_NAME = "ArcaneArmory-P1"  # change to your ESP32 name, or set to None


# ---------------------------
# Flask Update
# ---------------------------

def send_hp_delta(character_id: int, delta: int) -> None:
    """
    Sends a delta update to Flask.
    Flask will validate and clamp HP in the database.
    """
    try:
        payload = {"character_id": character_id, "delta": delta}
        r = requests.post(API_URL, json=payload, timeout=2)

        if r.status_code == 200:
            print(f"Updated character_id={character_id} by {delta}")
        else:
            print(f"API error {r.status_code}: {r.text}")

    except Exception as e:
        print("Connection error:", e)


# ---------------------------
# BLE Notification Handler
# ---------------------------

def on_notify(_: int, data: bytearray) -> None:
    """
    Called whenever the ESP32 sends a BLE notification.
    """
    try:
        msg = data.decode("utf-8").strip()
        # Expected: "P1:+1" or "P1:-1"
        player_key, delta_str = msg.split(":")
        delta = int(delta_str)

        character_id = PLAYER_TO_CHARACTER_ID.get(player_key)
        if character_id is None:
            print(f"Unknown player key: {player_key} (msg={msg})")
            return

        send_hp_delta(character_id, delta)

    except Exception as e:
        print("Bad BLE message:", data, e)


# ---------------------------
# BLE Main Loop
# ---------------------------

async def find_device():
    """
    Scan for BLE devices and return the target device.
    """
    devices = await BleakScanner.discover(timeout=5.0)

    for d in devices:
        if TARGET_DEVICE_NAME and d.name == TARGET_DEVICE_NAME:
            return d

    # Fallback: return first device advertising our service UUID (if available)
    # Note: Some platforms don't expose service UUIDs in scan results reliably.
    if not TARGET_DEVICE_NAME:
        for d in devices:
            if d.name and "ArcaneArmory" in d.name:
                return d

    return None


async def run():
    device = await find_device()
    if not device:
        print("ESP32 not found. Ensure it is powered and advertising.")
        return

    print(f"Connecting to {device.name} ({device.address})")

    while True:
        try:
            async with BleakClient(device.address) as client:
                print("Connected. Subscribing to notifications...")
                await client.start_notify(CHAR_EVENT_UUID, on_notify)

                while client.is_connected:
                    await asyncio.sleep(1)

        except Exception as e:
            print("BLE disconnected/error, retrying in 2 seconds:", e)
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run())