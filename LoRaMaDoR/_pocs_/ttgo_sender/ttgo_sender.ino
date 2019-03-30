/*
  This is a simple example show the LoRa sended data in OLED.

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
#define POWER   2 // dBm
#define PABOOST 1

unsigned int counter = 0;

SSD1306 display(0x3c, 4, 15);
String rssi = "RSSI --";
String packSize = "--";
String packet ;

void logo()
{
  display.clear();
  display.drawXbm(0,5,logo_width,logo_height,logo_bits);
  display.display();
}

void setup()
{
  pinMode(16,OUTPUT);
  pinMode(25,OUTPUT);
  
  digitalWrite(16, LOW);    // set GPIO16 low to reset OLED
  delay(50); 
  digitalWrite(16, HIGH); // while OLED is running, must set GPIO16 in high

  display.init();
  display.flipScreenVertically();  
  display.setFont(ArialMT_Plain_10);
  logo();
  delay(1500);
  display.clear();
  
  SPI.begin(SCK,MISO,MOSI,SS);
  LoRa.setPins(SS,RST,DI00);
  
  if (!LoRa.begin(BAND))
  {
    display.drawString(0, 0, "Starting LoRa failed!");
    display.display();
    while (1);
  }
  LoRa.setTxPower(POWER, PABOOST);
  LoRa.setSpreadingFactor(7);
  LoRa.setSignalBandwidth(125000);
  LoRa.setCodingRate4(5);
  LoRa.disableCrc();

  display.drawString(0, 0, "LoRa Initial success!");
  display.display();
  delay(1000);
}

static const int MSGSIZE = 80;
static const int REDUNDANCY = 20;
RS::ReedSolomon<MSGSIZE, REDUNDANCY> rs;
unsigned char message_frame[MSGSIZE];
unsigned char encoded_message[MSGSIZE + REDUNDANCY];

void loop()
{
  display.clear();
  display.setTextAlignment(TEXT_ALIGN_LEFT);
  display.setFont(ArialMT_Plain_10);
  
  display.drawString(0, 0, "send pkt ");
  display.drawString(90, 0, String(counter));
  display.display();

  String msg = "PU5EPX-1 LoRaMaDoR id " + String(counter);
  
  memset(message_frame, 0, sizeof(message_frame));
  int net_length = msg.length();
  for(int i = 0; i < msg.length() && i < MSGSIZE; i++) {
     message_frame[i] = msg[i];
  } 

  rs.Encode(message_frame, encoded_message);

  // send packet
  LoRa.beginPacket();
  for (int i = 0; i < net_length; ++i) {           
     LoRa.write(encoded_message[i]);
  }
  for (int i = 0; i < REDUNDANCY; ++i) {           
     LoRa.write(encoded_message[MSGSIZE + i]);
  }
  LoRa.endPacket();
  Serial.println("Sent packet " + msg);

  counter++;
  // digitalWrite(25, HIGH);   // turn the LED on (HIGH is the voltage level)
  // delay(1000);                       // wait for a second
  // digitalWrite(25, LOW);    // turn the LED off by making the voltage LOW
  delay(1000 + random(1000, 2000));                       // wait for a second
}
