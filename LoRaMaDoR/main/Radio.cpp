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

static bool setup_lora_common();

#ifndef __AVR__
static bool setup_lora()
{
	SPI.begin(SCK, MISO, MOSI, SS);
	return setup_lora_common();
}
#else
static bool setup_lora()
{
	return setup_lora_common();
}
#endif

static bool setup_lora_common()
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

#define ST_IDLE 0
#define ST_RX 1
#define ST_TX 2

static int status = ST_IDLE;

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
	if (status != ST_RX) {
		status = ST_RX;
		LoRa.receive();
	}
}

bool lora_tx(const Buffer& packet)
{
	if (status == ST_TX) {
		return false;
	}

	if (! LoRa.beginPacket()) {
		// can only fail if in tx mode, don't touch anything
		return false;
	}

	status = ST_TX;
	LoRa.write((uint8_t*) packet.cold(), packet.length());
	LoRa.endPacket(true);
	return true;
}

void lora_tx_done()
{
	status = ST_IDLE;
	lora_resume_rx();
}

void lora_start(void (*cb)(const char *buf, unsigned int plen, int rssi))
{
	rx_callback = cb;
	setup_lora();
	LoRa.onReceive(on_receive);
	LoRa.onTxDone(lora_tx_done);
	lora_resume_rx();
}
