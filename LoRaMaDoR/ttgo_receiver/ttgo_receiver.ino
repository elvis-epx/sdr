/*
  This is a simple example show the LoRa recived data in OLED.

  The onboard OLED display is SSD1306 driver and I2C interface. In order to make the
  OLED correctly operation, you should output a high-low-high(1-0-1) signal by soft-
  ware to OLED's reset pin, the low-level signal at least 5ms.

  OLED pins to ESP32 GPIOs via this connecthin:
  OLED_SDA -- GPIO4
  OLED_SCL -- GPIO15
  OLED_RST -- GPIO16
  
  by Aaron.Lee from HelTec AutoMation, ChengDu, China
  成都惠利特自动化科技有限公司
  www.heltec.cn
  
  this project also realess in GitHub:
  https://github.com/Heltec-Aaron-Lee/WiFi_Kit_series
*/
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
#define POWER 20
#define PABOOST 1

SSD1306 display(0x3c, 4, 15);
String rssi = "RSSI --";
String grossSize = "--";
String netSize = "--";

void logo(){
  display.clear();
  display.drawXbm(0,5,logo_width,logo_height,logo_bits);
  display.display();
}

void setup() {
  Serial.begin(9600);
  // while (!Serial);
  // Serial.println("Starting...");
  
  pinMode(16,OUTPUT);
  digitalWrite(16, LOW);    // set GPIO16 low to reset OLED
  delay(50); 
  digitalWrite(16, HIGH); // while OLED is running, must set GPIO16 in high、
  display.init();
  display.flipScreenVertically();  
  display.setFont(ArialMT_Plain_10);
  logo();
  delay(1000);
  display.clear();
  
  SPI.begin(SCK,MISO,MOSI,SS);
  LoRa.setPins(SS,RST,DI00);
  
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
  
  LoRa.onReceive(onReceive);
  LoRa.receive();
  // Serial.println("Waiting for packets");
}

int pcount = 0;
int dcount = 0;

void loop() {
  if (pcount > dcount) {
    loraData();
    dcount = pcount;
  }
}

static const int MSGSIZE = 80;
static const int REDUNDANCY = 20;
RS::ReedSolomon<MSGSIZE, REDUNDANCY> rs;
char decoded[MSGSIZE];
char encoded[MSGSIZE + REDUNDANCY];
char punctured[MSGSIZE + REDUNDANCY];
String msg;

void loraData()
{
  display.clear();
  display.setTextAlignment(TEXT_ALIGN_LEFT);
  display.setFont(ArialMT_Plain_10);
  display.drawString(0 , 15, "Recv #" + String(pcount) + " = " + grossSize);
  display.drawStringMaxWidth(0 , 30, 128, msg);
  display.drawString(0, 0, rssi);  
  display.display();
}

void onReceive(int plen) {
  // Serial.println("onReceive");
  ++pcount;
  rssi = "RSSI " + String(LoRa.packetRssi(), DEC);
  // Serial.println(rssi);
  grossSize = String(plen, DEC);
  // Serial.println(grossSize);
  int llen = plen - REDUNDANCY;
  netSize = String(llen, DEC);
  // Serial.println(netSize);

  if (plen > (MSGSIZE + REDUNDANCY)) {
    rssi += " too big";
    loraData();
    return;
  }
  if (plen <= REDUNDANCY) {
    rssi += " too small";
    loraData();
    return;
  }

  // Serial.println("Clearing");
  memset(punctured, 0, sizeof(punctured));
  memset(encoded, 0, sizeof(encoded));
  memset(decoded, 0, sizeof(decoded));

  // Serial.println("Recv octets");
  for (int i = 0; i < plen && i < sizeof(punctured); i++) {
      punctured[i] = LoRa.read();
  }

  // Serial.println("Unpuncturing");
  memcpy(encoded, punctured, llen);
  memcpy(encoded + MSGSIZE, punctured + llen, REDUNDANCY);

  // Serial.println("Decoding");
  if (rs.Decode(encoded, decoded)) {
      rssi += " corrupted";
      msg = "corrupted";
  } else {
      msg = decoded;
  }

  // Serial.println(msg);
}

