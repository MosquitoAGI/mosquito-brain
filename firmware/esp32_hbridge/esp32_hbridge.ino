/*
 * esp32_hbridge — disarmed receiver scaffold.
 *
 * Receives motor_command datagrams, validates them, and stops the motors when
 * the stream goes quiet. The two functions that would move a robot are stubs:
 * see README.md before you flash this at anything.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

#define WIFI_SSID "TODO"
#define WIFI_PASS "TODO"

static const uint16_t COMMAND_PORT = 9000;
static const uint16_t TELEMETRY_PORT = 9001;
static const uint16_t MAX_PACKET = 512;
static const uint32_t COMMAND_TIMEOUT_MS = 500;
static const uint32_t TELEMETRY_PERIOD_MS = 50;

WiFiUDP udp;
IPAddress pcAddress(192, 168, 4, 2);

char packet[MAX_PACKET + 1];
uint32_t lastCommandMs = 0;
uint32_t lastTelemetryMs = 0;
uint32_t tripCount = 0;
long lastSequence = -1;
bool stopped = true;

// ---------------------------------------------------------------- hardware --
// TODO: implement for your driver board. Keep the range -100..100.
void setMotorSpeed(uint8_t channel, float value) {
  (void)channel;
  (void)value;
}

// TODO: implement. Fill three axis readings in radians per second.
void readIMU(float *gyro) {
  gyro[0] = 0.0f;
  gyro[1] = 0.0f;
  gyro[2] = 0.0f;
}

void stopMotors() {
  setMotorSpeed(0, 0.0f);
  setMotorSpeed(1, 0.0f);
  stopped = true;
}

// ----------------------------------------------------------------- parsing --
// A small, strict extractor: it looks for a key and returns false rather than
// guessing. Not a general JSON parser, on purpose — the payload is fixed.
bool numberFor(const char *json, const char *key, float *out) {
  const char *at = strstr(json, key);
  if (at == nullptr) return false;
  at = strchr(at, ':');
  if (at == nullptr) return false;
  char *end = nullptr;
  float value = strtof(at + 1, &end);
  if (end == at + 1) return false;
  if (!isfinite(value)) return false;
  if (value < -100.0f || value > 100.0f) return false;
  *out = value;
  return true;
}

bool longFor(const char *json, const char *key, long *out) {
  const char *at = strstr(json, key);
  if (at == nullptr) return false;
  at = strchr(at, ':');
  if (at == nullptr) return false;
  char *end = nullptr;
  long value = strtol(at + 1, &end, 10);
  if (end == at + 1) return false;
  *out = value;
  return true;
}

void handleCommand(const char *json, size_t length, IPAddress from) {
  if (length == 0 || length > MAX_PACKET) return;
  if (strstr(json, "\"motor_command\"") == nullptr) return;

  float left = 0.0f;
  float right = 0.0f;
  long sequence = -1;
  if (!numberFor(json, "\"left\"", &left)) return;
  if (!numberFor(json, "\"right\"", &right)) return;
  if (!longFor(json, "\"sequence\"", &sequence)) return;
  if (sequence <= lastSequence) return;  // duplicate or replayed packet
  lastSequence = sequence;

  pcAddress = from;
  lastCommandMs = millis();
  stopped = false;
  setMotorSpeed(0, left);
  setMotorSpeed(1, right);
}

void sendTelemetry() {
  float gyro[3] = {0.0f, 0.0f, 0.0f};
  readIMU(gyro);
  char out[192];
  snprintf(out, sizeof(out),
           "{\"type\":\"telemetry\",\"sequence\":%lu,\"gyro\":[%.4f,%.4f,%.4f],"
           "\"accel\":[0,0,1],\"left_speed\":0,\"right_speed\":0}",
           (unsigned long)(lastTelemetryMs / TELEMETRY_PERIOD_MS + 1), gyro[0], gyro[1], gyro[2]);
  udp.beginPacket(pcAddress, TELEMETRY_PORT);
  udp.write((const uint8_t *)out, strlen(out));
  udp.endPacket();
}

// -------------------------------------------------------------------- setup --
void setup() {
  Serial.begin(115200);
  stopMotors();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
    Serial.print(".");
  }
  Serial.printf("\nbridge listening on %u\n", COMMAND_PORT);
  udp.begin(COMMAND_PORT);
  lastCommandMs = millis();
}

void loop() {
  int size = udp.parsePacket();
  if (size > 0) {
    int read = udp.read(packet, MAX_PACKET);
    if (read > 0) {
      packet[read] = '\0';
      handleCommand(packet, (size_t)read, udp.remoteIP());
    }
  }

  const uint32_t now = millis();
  if (!stopped && (now - lastCommandMs) > COMMAND_TIMEOUT_MS) {
    stopMotors();
    tripCount++;
    Serial.printf("watchdog trip %lu\n", (unsigned long)tripCount);
  }
  if ((now - lastTelemetryMs) >= TELEMETRY_PERIOD_MS) {
    lastTelemetryMs = now;
    sendTelemetry();
  }
}
