#ifndef UNDER_TEST
#ifndef __AVR__
#include <SPI.h>
#endif

#include <LoRa.h>
#endif

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "RS-FEC.h"
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
static void lora_resume_rx();
static void loraip_rx_pre(const char *data, unsigned int len);

#ifdef UNDER_TEST
bool setup_lora()
{
	return setup_lora_common();
}
#else
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
#endif

static bool setup_lora_common()
{
#ifndef UNDER_TEST
	LoRa.setPins(SS, RST, DIO0);

	if (!LoRa.begin(BAND)) {
		return false;
	}

	LoRa.setTxPower(POWER, PABOOST);
	LoRa.setSpreadingFactor(SPREAD);
	LoRa.setSignalBandwidth(BWIDTH);
	LoRa.setCodingRate4(CR4SLSH);
	LoRa.disableCrc();
#endif
	lora_resume_rx();

	return true;
}

#ifdef UNDER_TEST
char testbuf[255];
unsigned int testbuflen;
#endif

static bool rx_enabled = false;
static char recv_area[255];

void _on_receive(int plen)
{
#ifdef UNDER_TEST
	memcpy(recv_area, testbuf, plen);
#else
	for (unsigned int i = 0; i < plen && i < sizeof(recv_area); i++) {
		recv_area[i] = LoRa.read();
	}
#endif
	loraip_rx_pre(recv_area, plen);
}

static void lora_resume_rx()
{
	if (!rx_enabled) {
		rx_enabled = true;
#ifndef UNDER_TEST
		LoRa.onReceive(_on_receive);
		LoRa.receive();
#endif
	}
}

static void lora_tx(const char *buf, unsigned int len)
{
	rx_enabled = false;
#ifndef UNDER_TEST
	LoRa.beginPacket();        
	LoRa.write(buf, len);
	LoRa.endPacket();
#else
	memset(testbuf, 0, sizeof(testbuf));
	memcpy(testbuf, buf, len);
	testbuflen = len;
#endif
	lora_resume_rx();
}

static const int MSGSIZE_SHORT = 80;
static const int MSGSIZE_LONG = 180;
static const int REDUNDANCY = 20;

char rs_encoded[MSGSIZE_LONG + REDUNDANCY];
char txbuf[MSGSIZE_LONG + REDUNDANCY];
char rs_decoded[MSGSIZE_LONG];

RS::ReedSolomon<MSGSIZE_LONG, REDUNDANCY> rs_long;
RS::ReedSolomon<MSGSIZE_SHORT, REDUNDANCY> rs_short;

static void loraip_rx_pre(const char *data, unsigned int len)
{
	if (len <= REDUNDANCY || len > (MSGSIZE_LONG + REDUNDANCY)) {
		return;
	}

	memset(rs_encoded, 0, sizeof(rs_encoded));
	if (len <= (MSGSIZE_SHORT + REDUNDANCY)) {
		memcpy(rs_encoded, data, len - REDUNDANCY);
		memcpy(rs_encoded + MSGSIZE_SHORT, data + len - REDUNDANCY, REDUNDANCY);
		if (rs_short.Decode(rs_encoded, rs_decoded)) {
#ifdef UNDER_TEST
			printf("rx_pre: corrupted packet\n");
#endif
			return;
		}
		loraip_rx(rs_decoded, len - REDUNDANCY);
	} else {
		memcpy(rs_encoded, data, len - REDUNDANCY);
		memcpy(rs_encoded + MSGSIZE_LONG, data + len - REDUNDANCY, REDUNDANCY);
		if (rs_long.Decode(rs_encoded, rs_decoded)) {
#ifdef UNDER_TEST
			printf("rx_pre: corrupted packet\n");
#endif
			return;
		}
		loraip_rx(rs_decoded, len - REDUNDANCY);
	}
}

void loraip_tx(const char *buf, unsigned int len)
{
	if (len > MSGSIZE_LONG) {
		return;
	}

	memset(rs_decoded, 0, sizeof(rs_decoded));
	memcpy(rs_decoded, buf, len);
	memcpy(txbuf, buf, len);

	if (len <= MSGSIZE_SHORT) {
		rs_short.Encode(rs_decoded, rs_encoded);
		memcpy(txbuf + len, rs_encoded + MSGSIZE_SHORT, REDUNDANCY);
	} else {
		rs_long.Encode(rs_decoded, rs_encoded);
		memcpy(txbuf + len, rs_encoded + MSGSIZE_LONG, REDUNDANCY);
	}

	lora_tx(txbuf, len + REDUNDANCY);
}
