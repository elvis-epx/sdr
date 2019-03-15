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
#define POWER 0
#define PABOOST 0

SSD1306 display(0x3c, 4, 15);
String rssi = "RSSI --";
String grossSize = "--";
String netSize = "--";

void logo(){
  display.clear();
  display.drawXbm(0,5,logo_width,logo_height,logo_bits);
  display.display();
}

static const int MSGSIZE = 80;
static const int REDUNDANCY = 20;
RS::ReedSolomon<MSGSIZE, REDUNDANCY> rs;
char message_frame[MSGSIZE + 1];
char punctured_message[128];
char encoded_message_u[MSGSIZE + REDUNDANCY];
String msg;

void loraData(){
  display.clear();
  display.setTextAlignment(TEXT_ALIGN_LEFT);
  display.setFont(ArialMT_Plain_10);
  display.drawString(0 , 15 , "Recv octets "+ grossSize + " " + netSize);
  display.drawStringMaxWidth(0 , 26 , 128, msg);
  display.drawString(0, 0, rssi);  
  display.display();
}

void cbk(int plen) {
  rssi = "RSSI " + String(LoRa.packetRssi(), DEC);
  grossSize = String(plen, DEC);
  // message length = packet length - redundancy size
  int llen = plen - REDUNDANCY;
  netSize = String(llen, DEC);

  if (plen > (MSGSIZE + REDUNDANCY)) {
    rssi += " too big";
    loraData();
    return;
  }

  memset(punctured_message, 0, sizeof(punctured_message));

  for (int i = 0; i < plen && i < sizeof(punctured_message); i++) {
      punctured_message[i] = LoRa.read();
  }

  // unpuncture
  memset(encoded_message_u, 0, sizeof(encoded_message_u));
  memcpy(encoded_message_u, punctured_message, llen);
  memcpy(encoded_message_u + MSGSIZE, punctured_message + llen, REDUNDANCY);

  if (rs.Decode(encoded_message_u, message_frame)) {
      rssi += " corrupted";
      msg = "";
  } else {
      msg = String(message_frame);
  }
   
  loraData();
}

void setup() {
  pinMode(16,OUTPUT);
  digitalWrite(16, LOW);    // set GPIO16 low to reset OLED
  delay(50); 
  digitalWrite(16, HIGH); // while OLED is running, must set GPIO16 in high、
  display.init();
  display.flipScreenVertically();  
  display.setFont(ArialMT_Plain_10);
  logo();
  delay(1500);
  display.clear();
  
  SPI.begin(SCK,MISO,MOSI,SS);
  LoRa.setPins(SS,RST,DI00);
  
  if (!LoRa.begin(BAND)) {
    display.drawString(0, 0, "Starting LoRa failed!");
    display.display();
    while (1);
  }
  LoRa.setSpreadingFactor(9);
  LoRa.setTxPower(POWER, PABOOST);
  LoRa.setSignalBandwidth(125000);
  LoRa.setCodingRate4(5);
  LoRa.disableCrc();
  
  display.drawString(0, 0, "LoRa Initial success!");
  display.drawString(0, 10, "Wait for incomm data...");
  display.display();
  delay(10000);
  //LoRa.onReceive(cbk);
  LoRa.receive();
}


void loop() {
  int packetSize = LoRa.parsePacket();
  if (packetSize) { cbk(packetSize);  }
  delay(10);
}
