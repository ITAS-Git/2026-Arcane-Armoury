import asyncio
import requests
from bleak import BleakClient, BleakScanner

API_URL = "http://localhost:5000/api/hp_delta_current_turn"
CHAR_EVENT_UUID = "8f3a2f11-6c5f-4c3d-a9a0-222222222222"
TARGET_DEVICE_NAME = "ArcaneArmory-P1"


def send_hp_delta(delta: int) -> None:
    try:
        payload = {"delta": delta}
        r = requests.post(API_URL, json=payload, timeout=2)

        if r.status_code == 200:
            try:
                response = r.json()
                print(
                    f"Updated {response.get('playerName', 'current player')} "
                    f"by {delta}. HP is now {response.get('hp')}/{response.get('maxHp')}"
                )
            except Exception:
                print(f"Updated current-turn player by {delta}")
        else:
            print(f"API error {r.status_code}: {r.text}")

    except Exception as e:
        print("Connection error:", e)


def on_notify(_: int, data: bytearray) -> None:
    try:
        msg = data.decode("utf-8").strip()
        print("BLE message:", msg)

        delta = int(msg)
        if delta not in (-1, 1):
            print(f"Ignoring unsupported delta: {delta}")
            return

        send_hp_delta(delta)

    except Exception as e:
        print("Bad BLE message:", data, e)


async def find_device():
    devices = await BleakScanner.discover(timeout=5.0)

    for d in devices:
        if TARGET_DEVICE_NAME and d.name == TARGET_DEVICE_NAME:
            return d

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
        client = None
        try:
            client = BleakClient(device.address)
            await client.connect()
            print("Connected. Subscribing to notifications...")

            await client.start_notify(CHAR_EVENT_UUID, on_notify)

            while client.is_connected:
                await asyncio.sleep(1)

        except Exception as e:
            print("BLE disconnected/error, retrying in 2 seconds:", e)

        finally:
            if client is not None:
                try:
                    if client.is_connected:
                        await client.stop_notify(CHAR_EVENT_UUID)
                except Exception:
                    pass

                try:
                    if client.is_connected:
                        await client.disconnect()
                except Exception:
                    pass

            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run())
