#ifndef __AVR__
#include <SPI.h>
#endif
#include <LoRa.h>
#include "Radio.h"

#ifndef __AVR__

// Pin defintion of WIFI LoRa 32
// HelTec AutoMation 2017 support@heltec.cn 
#define SCK     5    // GPIO5  -- SX127x's SCK
#define MISO    19   // GPIO19 -- SX127x's MISO
#define MOSI    27   // GPIO27 -- SX127x's MOSI

#define SS      18   // GPIO18 -- SX127x's CS
#define RST     14   // GPIO14 -- SX127x's RESET
#define DIO0    26   // GPIO26 -- SX127x's IRQ(Interrupt Request)

#else

#define SS 8
#define RST 4
#define DIO0 7

#endif

/* LoRa parameters */
#define BAND    916750000
#define POWER   20
#define PABOOST 1
#define SPREAD  9
#define BWIDTH  62500
#define CR4SLSH 5

bool setup_lora_common();

#ifndef __AVR__
bool setup_lora()
{
	SPI.begin(SCK, MISO, MOSI, SS);
	return setup_lora_common();
}
#else
bool setup_lora()
{
	return setup_lora_common();
}
#endif

bool setup_lora_common()
{
	LoRa.setPins(SS, RST, DIO0);

	if (!LoRa.begin(BAND)) {
		return false;
	}

	LoRa.setTxPower(POWER, PABOOST);
	LoRa.setSpreadingFactor(SPREAD);
	LoRa.setSignalBandwidth(BWIDTH);
	LoRa.setCodingRate4(CR4SLSH);
	LoRa.disableCrc();

	return true;
}

char recv_area[255];
void (*callback)(const char *, unsigned int, int) = 0;

static void on_receive(int plen)
{
	int rssi = LoRa.packetRssi();
	for (unsigned int i = 0; i < plen && i < sizeof(recv_area); i++) {
		recv_area[i] = LoRa.read();
	}
	if (callback) {
		callback(recv_area, plen, rssi);
	}
}

void lora_rx(void (*cb)(const char *buf, unsigned int plen, int rssi))
{
	callback = cb;
	LoRa.onReceive(on_receive);
	LoRa.receive();
}

int lora_tx(const Buffer& packet)
{
	LoRa.beginPacket();        
	LoRa.write((uint8_t*) packet.rbuf(), packet.length());      
	long int t0 = millis();
	LoRa.endPacket();
	long int t1 = millis();
	return t1 - t0;
}
