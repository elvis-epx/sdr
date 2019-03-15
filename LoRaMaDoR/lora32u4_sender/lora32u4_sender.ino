
#include <SPI.h>              // include libraries
#include <LoRa.h>
#include <RS-FEC.h>

const int csPin = 8;          // LoRa radio chip select
const int resetPin = 4;       // LoRa radio reset
const int irqPin = 7;         // change for your board; must be a hardware interrupt pin

byte msgCount = 0;            // count of outgoing messages
long lastSendTime = millis();        // last send time
int interval = 3000;      

int led = LOW;

#define POWER   0 // dBm
#define PABOOST 1

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, led);
  
  Serial.begin(9600);                   // initialize serial
  // while (!Serial);

  Serial.println("LoRa Duplex");

  // override the default CS, reset, and IRQ pins (optional
  LoRa.setPins(csPin, resetPin, irqPin);// set CS, reset, IRQ pin

  if (!LoRa.begin(916750000)) { 
    Serial.println("LoRa init failed. Check your connections.");
    while (true); 
  }
  
  LoRa.setTxPower(POWER, PABOOST);
  LoRa.setSpreadingFactor(9);
  LoRa.setSignalBandwidth(125000);
  LoRa.setCodingRate4(5);
  LoRa.disableCrc();

  Serial.println("LoRa init succeeded.");
}

void loop() {
  if (millis() - lastSendTime > interval) {
    Serial.println("Preparing");
    sendMessage();
    lastSendTime = millis();
    interval = 2000;
  }
}

static const int MSGSIZE = 80;
static const int REDUNDANCY = 20;
RS::ReedSolomon<MSGSIZE, REDUNDANCY> rs;
unsigned char message[MSGSIZE];
unsigned char encoded[MSGSIZE + REDUNDANCY];

void sendMessage() {
  led = !led;
  digitalWrite(LED_BUILTIN, led);

  String msg = "PU5EPX-3 LoRaMaDoR id " + String(msgCount);

  memset(message, 0, sizeof(message));
  for(unsigned int i = 0; i < msg.length(); i++) {
     message[i] = msg[i];
  } 

  Serial.println("Encoding...");
  rs.Encode(message, encoded);
  Serial.println("Sending...");
 
  LoRa.beginPacket();
  for (int i = 0; i < msg.length(); ++i) {           
     LoRa.write(encoded[i]);
  }
  for (int i = 0; i < REDUNDANCY; ++i) {           
     LoRa.write(encoded[MSGSIZE + i]);
  }
  long t0 = millis();
  LoRa.endPacket(); 
  long t1 = millis();
  Serial.print("Time to send packet: ");
  Serial.println(t1 - t0);
  msgCount++;                           // increment message ID
}
