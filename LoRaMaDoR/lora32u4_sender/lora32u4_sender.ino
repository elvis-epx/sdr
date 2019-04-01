// Use a LoRa32u4 as beacon sender for tests
// Even though the LoRa32u4 has a better crystal than TTGO
// and could go down to 31.25kHz bandwidth, the 32u4 can't
// even load a program with proper packet encoding and decoding,
// so we need to make veeeery simple to even use 32u4 as a
// simple beacon for distance reach tests :(

#include <SPI.h>              // include libraries
#include <LoRa.h>
#include <RS-FEC.h>

const int csPin = 8;          // LoRa radio chip select
const int resetPin = 4;       // LoRa radio reset
const int irqPin = 7;         // change for your board; must be a hardware interrupt pin

long int msgCount = 0;            // count of outgoing messages
long lastSendTime = millis();        // last send time
int interval = 10000;      

#define POWER   20 // dBm
#define PABOOST 1

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
 
  Serial.begin(9600);
  Serial.println("LoRa");
  LoRa.setPins(csPin, resetPin, irqPin);

  if (!LoRa.begin(916750000)) { 
    Serial.println("LoRa init failed. Check your connections.");
    while (true); 
  }
  
  LoRa.setTxPower(POWER, PABOOST);
  LoRa.setSpreadingFactor(9);
  LoRa.setSignalBandwidth(62500);
  LoRa.setCodingRate4(5);
  LoRa.disableCrc();

  Serial.println("LoRa init succeeded.");
}

void loop() {
  if (millis() - lastSendTime > interval) {
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.println("Preparing");
    sendMessage();
    lastSendTime = millis();
    interval = 10000;
  }
}

static const int MSGSIZE = 80;
static const int REDUNDANCY = 20;
RS::ReedSolomon<MSGSIZE, REDUNDANCY> rs;
unsigned char message[MSGSIZE];
unsigned char encoded[MSGSIZE + REDUNDANCY];

void sendMessage() {
  digitalWrite(LED_BUILTIN, LOW);

  String msg = "QB<PU5EPX-3:" + String(++msgCount) + " LoRaMaDoR 73";
  
  memset(message, 0, sizeof(message));
  for(unsigned int i = 0; i < msg.length() && i < MSGSIZE; i++) {
     message[i] = msg[i];
  } 

  rs.Encode(message, encoded);
  Serial.println("Sending...");
 
  LoRa.beginPacket();        
  LoRa.write(encoded, msg.length());      
  LoRa.write(encoded + MSGSIZE, REDUNDANCY);

  digitalWrite(LED_BUILTIN, HIGH);
  LoRa.endPacket();
  digitalWrite(LED_BUILTIN, LOW);
}
