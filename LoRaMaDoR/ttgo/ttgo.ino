#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <RS-FEC.h>
#include "SSD1306.h" 
#include "images.h"

// Pin definetion of WIFI LoRa 32
// HelTec AutoMation 2017 support@heltec.cn 
#define SCK     5    // GPIO5  -- SX127x's SCK
#define MISO    19   // GPIO19 -- SX127x's MISO
#define MOSI    27   // GPIO27 -- SX127x's MOSI
#define SS      18   // GPIO18 -- SX127x's CS
#define RST     14   // GPIO14 -- SX127x's RESET
#define DI00    26   // GPIO26 -- SX127x's IRQ(Interrupt Request)

#define BAND    916750000  //you can set band here directly,e.g. 868E6,915E6
#define POWER   20 // dBm
#define PABOOST 1

long int msgCount = 0; 
long lastSendTime = millis();

SSD1306 display(0x3c, 4, 15);
String rssi = "RSSI --";
String packSize = "--";
String packet ;

void setup()
{
  Serial.begin(9600);
  pinMode(16,OUTPUT);
  pinMode(25,OUTPUT);
  
  digitalWrite(16, LOW);    // set GPIO16 low to reset OLED
  delay(50); 
  digitalWrite(16, HIGH); // while OLED is running, must set GPIO16 in high
    
  SPI.begin(SCK,MISO,MOSI,SS);
  LoRa.setPins(SS,RST,DI00);

  display.init();
  display.flipScreenVertically();  
  display.setFont(ArialMT_Plain_10);

  if (!LoRa.begin(BAND)) {
    display.drawString(0, 0, "Starting LoRa failed!");
    display.display();
    while (1);
  }
  
  LoRa.setTxPower(POWER, PABOOST);
  LoRa.setSpreadingFactor(9);
  LoRa.setSignalBandwidth(62500);
  LoRa.setCodingRate4(5);
  LoRa.disableCrc();

  display.drawString(0, 0, "LoRa ok");
  display.display();
}

static const int MSGSIZE = 80;
static const int REDUNDANCY = 20;
RS::ReedSolomon<MSGSIZE, REDUNDANCY> rs;
unsigned char message[MSGSIZE];
unsigned char encoded[MSGSIZE + REDUNDANCY];

void loop() {
  if (millis() > (lastSendTime + 5000)) {
    sendMessage();
    lastSendTime = millis();
  }
}

void sendMessage() {
  String msg = "QB<PU5EPX:" + String(++msgCount) + " LoRaMaDoR 73 ";
  // Serial.println(msg);

  memset(message, 0, sizeof(message));
  for(unsigned int i = 0; i < msg.length() && i < MSGSIZE; i++) {
     message[i] = msg[i];
  } 

  rs.Encode(message, encoded);
  
  LoRa.beginPacket();        
  LoRa.write(encoded, msg.length());      
  LoRa.write(encoded + MSGSIZE, REDUNDANCY);
  long int t0 = millis();
  LoRa.endPacket();
  long int t1 = millis();

  // Serial.println("Send in " + String(t1 - t0) + "ms");

  display.clear();
  display.setTextAlignment(TEXT_ALIGN_LEFT);
  display.setFont(ArialMT_Plain_10);
  display.drawString(0, 0, "Sending #" + String(msgCount));
  display.setFont(ArialMT_Plain_10);
  display.drawString(0, 10, "Sent " + String(msg.length() + REDUNDANCY) + " bytes in " + String(t1 - t0) + "ms");
  display.display();
}
