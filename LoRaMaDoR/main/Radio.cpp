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

unsigned long int lora_speed_bps()
{
	unsigned long int bps = BWIDTH;
	bps *= SPREAD;
	bps *= 4;
	bps /= CR4SLSH;
	bps /= (1 << SPREAD);
	return bps;
}

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

static bool rx_enabled = false;
static char recv_area[255];
static void (*rx_callback)(const char *, unsigned int, int) = 0;

static void on_receive(int plen)
{
	int rssi = LoRa.packetRssi();
	for (unsigned int i = 0; i < plen && i < sizeof(recv_area); i++) {
		recv_area[i] = LoRa.read();
	}
	if (rx_callback) {
		rx_callback(recv_area, plen, rssi);
	}
}

void lora_resume_rx()
{
	if (!rx_enabled) {
		rx_enabled = true;
		if (rx_callback) {
			LoRa.onReceive(on_receive);
			LoRa.receive();
		} else {
			LoRa.idle();
		}
	}
}

void lora_rx(void (*cb)(const char *buf, unsigned int plen, int rssi))
{
	rx_callback = cb;
	lora_resume_rx();
}

int lora_tx(const Buffer& packet)
{
	rx_enabled = false;
	LoRa.beginPacket();        
	LoRa.write((uint8_t*) packet.cold(), packet.length());      
	long int t0 = millis();
	LoRa.endPacket();
	long int t1 = millis();
	lora_resume_rx();
	return t1 - t0;
}
