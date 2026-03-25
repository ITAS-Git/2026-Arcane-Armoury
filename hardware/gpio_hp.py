import asyncio
import requests
from bleak import BleakClient, BleakScanner

API_URL = "http://localhost:5000/api/hp_delta"
STATE_URL = "http://localhost:5000/api/state"

SERVICE_UUID = "8f3a2f10-6c5f-4c3d-a9a0-111111111111"
CHAR_EVENT_UUID = "8f3a2f11-6c5f-4c3d-a9a0-222222222222"
TARGET_DEVICE_NAME = "ArcaneArmory-P1"


def get_current_player() -> int:
    """Fetch the current turn index from Flask and return player number (1-4)."""
    try:
        r = requests.get(STATE_URL, timeout=2)
        if r.status_code == 200:
            data = r.json()
            return int(data.get("turnIndex", 0)) + 1  # turnIndex is 0-based
    except Exception as e:
        print("Could not fetch state:", e)
    return 1  # fallback to player 1


def send_hp_delta(delta: int) -> None:
    player = get_current_player()
    try:
        payload = {"player": player, "delta": delta}
        r = requests.post(API_URL, json=payload, timeout=2)
        if r.status_code == 200:
            print(f"Updated player {player} by {delta:+}")
        else:
            print(f"API error {r.status_code}: {r.text}")
    except Exception as e:
        print("Connection error:", e)


def on_notify(_: int, data: bytearray) -> None:
    print("RAW BLE DATA:", data)
    try:
        msg = data.decode("utf-8").strip()
        print("DECODED:", msg)
        _, delta_str = msg.split(":")
        delta = max(-100, min(100, int(delta_str)))
        send_hp_delta(delta)
    except Exception as e:
        print("Bad BLE message:", data, e)


async def find_device():
    devices = await BleakScanner.discover(timeout=5.0)
    for d in devices:
        if TARGET_DEVICE_NAME and d.name == TARGET_DEVICE_NAME:
            return d
    if not TARGET_DEVICE_NAME:
        for d in devices:
            if d.name and "ArcaneArmory" in d.name:
                return d
    return None


async def run():
    device = await find_device()
    if not device:
        print("ESP32 not found.")
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
