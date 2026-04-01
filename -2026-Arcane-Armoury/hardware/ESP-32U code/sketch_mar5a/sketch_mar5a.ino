/**
 * Arcane Armory – ESP32 BLE Button Controller
 *
 * Sends BLE notifications to the Python bridge when UP or DOWN
 * buttons are pressed.
 *
 * Notification format: "+1" or "-1"
 *
 * UUIDs must match SERVICE_UUID / CHAR_EVENT_UUID in gpio_hp.py.
 *
 * Author: Alexander Preston
 * Course: ITAS 164
 */

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ---------------------------
// DEVICE CONFIG
// ---------------------------
#define DEVICE_NAME  "ArcaneArmory-P1"

// ---------------------------
// BLE UUIDs — must match gpio_hp.py
// ---------------------------
#define SERVICE_UUID  "8f3a2f10-6c5f-4c3d-a9a0-111111111111"
#define CHAR_UUID     "8f3a2f11-6c5f-4c3d-a9a0-222222222222"

// ---------------------------
// GPIO PINS
// ---------------------------
const int BUTTON_UP   = 19;
const int BUTTON_DOWN = 15;

// ---------------------------
// DEBOUNCE
// ---------------------------
const unsigned long DEBOUNCE_MS = 50;

int lastUpState = HIGH;
int lastDownState = HIGH;
unsigned long lastUpTime = 0;
unsigned long lastDownTime = 0;

// ---------------------------
// BLE STATE
// ---------------------------
BLECharacteristic* pCharacteristic = nullptr;
bool deviceConnected = false;

// Restart advertising when a client disconnects
class ArmoryServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) override {
    deviceConnected = true;
    Serial.println("[BLE] Client connected");
  }

  void onDisconnect(BLEServer* pServer) override {
    deviceConnected = false;
    Serial.println("[BLE] Client disconnected, restarting advertising");
    delay(500);
    pServer->startAdvertising();
  }
};

// ---------------------------
// HELPERS
// ---------------------------

void sendNotify(const char* msg) {
  if (!deviceConnected || pCharacteristic == nullptr) {
    Serial.print("[BLE] Not connected, dropped: ");
    Serial.println(msg);
    return;
  }

  pCharacteristic->setValue((uint8_t*)msg, strlen(msg));
  pCharacteristic->notify();

  Serial.print("[BLE] Sent: ");
  Serial.println(msg);
}

void sendDelta(int delta) {
  char msg[4];
  snprintf(msg, sizeof(msg), "%+d", delta);  // "+1" or "-1"
  sendNotify(msg);
}

// ---------------------------
// SETUP
// ---------------------------
#include "esp_gap_ble_api.h"

void setup() {
  Serial.begin(115200);

  BLEDevice::init(DEVICE_NAME);

  //Increase BLE transmit power (MAX)
  esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_DEFAULT, ESP_PWR_LVL_P9);
  esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_ADV, ESP_PWR_LVL_P9);
  esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_SCAN, ESP_PWR_LVL_P9);

  pinMode(BUTTON_UP, INPUT_PULLUP);
  pinMode(BUTTON_DOWN, INPUT_PULLUP);



  BLEServer* pServer = BLEDevice::createServer();
  pServer->setCallbacks(new ArmoryServerCallbacks());

  BLEService* pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
    CHAR_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();

  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->start();

  Serial.print("[BLE] Advertising as: ");
  Serial.println(DEVICE_NAME);
}

// ---------------------------
// LOOP
// ---------------------------
void loop() {
  unsigned long now = millis();

  int upState = digitalRead(BUTTON_UP);
  int downState = digitalRead(BUTTON_DOWN);

  if (upState == LOW && lastUpState == HIGH) {
    if (now - lastUpTime >= DEBOUNCE_MS) {
      sendDelta(+1);
      lastUpTime = now;
    }
  }
  lastUpState = upState;

  if (downState == LOW && lastDownState == HIGH) {
    if (now - lastDownTime >= DEBOUNCE_MS) {
      sendDelta(-1);
      lastDownTime = now;
    }
  }
  lastDownState = downState;

  delay(5);
}
