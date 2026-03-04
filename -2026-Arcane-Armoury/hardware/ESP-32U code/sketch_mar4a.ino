const int buttonPinDown = 16;
const int buttonPinUp   = 18;

int lastDownState = HIGH;
int lastUpState   = HIGH;

void setup() {
    Serial.begin(115200);

    pinMode(buttonPinDown, INPUT_PULLUP);
    pinMode(buttonPinUp, INPUT_PULLUP);
}

void loop() {
    int downState = digitalRead(buttonPinDown);
    int upState   = digitalRead(buttonPinUp);

    // DOWN button pressed
    if (downState == LOW && lastDownState == HIGH) {
        Serial.println("DOWN");
    }

    // UP button pressed
    if (upState == LOW && lastUpState == HIGH) {
        Serial.println("UP");
    }

    lastDownState = downState;
    lastUpState = upState;

    delay(10); // small debounce
}