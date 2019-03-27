#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include "SSD1306.h"
#include "Packet.h"

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

// use button to toogle this.
const bool SEND_BEACON = true;
const long int AVG_BEACON_TIME = 10000;

const char *my_prefix = "PU5EPX-1";

long int ident = 0; 
long nextSendTime = millis() + 1000;

int recv_pcount = 0;
int recv_dcount = 0;

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
  
  LoRa.onReceive(onReceive);
  LoRa.receive();
}

void loop()
{
	if (SEND_BEACON) {
		if (millis() > nextSendTime) {
			sendMessage();
			long int next = random(AVG_BEACON_TIME / 2,
						AVG_BEACON_TIME * 3 / 2);
			nextSendTime = millis() + next;
      return;
		}
	}
  if (recv_pcount > recv_dcount) {
    recv_dcount = recv_pcount;
    recv_show();
  }
}

void sendMessage()
{
  ident %= 999;
  ++ident;
	Buffer msg = "LoRaMaDoR 73.";
	Packet p = Packet("QB", my_prefix, ident, Dict(), msg);
	Buffer encoded = p.encode_l2();

	LoRa.beginPacket();        
	LoRa.write((uint8_t*) encoded.rbuf(), encoded.length());      
	long int t0 = millis();
	LoRa.endPacket();
	long int t1 = millis();
  LoRa.receive();

	// Serial.println("Send in " + String(t1 - t0) + "ms");

	display.clear();
	display.setTextAlignment(TEXT_ALIGN_LEFT);
	display.setFont(ArialMT_Plain_10);
	display.drawString(0, 0, "Sending #" + String(ident));
	display.setFont(ArialMT_Plain_10);
	display.drawString(0, 10, "Sent " + String(encoded.length()) + " bytes in " + String(t1 - t0) + "ms");
	display.display();
}

int recv_rssi;
String recv_from;
String recv_to;
unsigned long int recv_ident;
String recv_params;
String recv_msg;

char recv_area[255];

void onReceive(int plen)
{
  // Serial.println("onReceive");
  ++recv_pcount;
  recv_rssi = LoRa.packetRssi();
  for (int i = 0; i < plen && i < sizeof(recv_area); i++) {
    recv_area[i] = LoRa.read();
  }
  Packet *p = Packet::decode_l2(recv_area, plen);
  if (!p) {
    recv_from = "";
    recv_to = "";
    recv_ident = 0;
    recv_params = "";
    recv_msg = ">>> Corrupted " + String(Packet::get_decode_error());
    return;
  }
  
  recv_from = p->from();
  recv_to = p->to();
  recv_ident = p->ident();
  recv_params = p->sparams();
  recv_msg = p->msg().rbuf();
  delete p;
}

void recv_show()
{
  display.clear();
  display.setTextAlignment(TEXT_ALIGN_LEFT);
  display.setFont(ArialMT_Plain_10);
  display.drawString(0, 0, "Recv #" + String(recv_pcount) + " RSSI " + String(recv_rssi)); 
  display.drawString(0, 12, recv_to + " < " + recv_from);
  display.drawString(0, 24, "Ident " + String(recv_ident));
  display.drawString(0, 36, "Params " + recv_params);
  display.drawStringMaxWidth(0 , 48, 80, recv_msg); 
  display.display();
}

