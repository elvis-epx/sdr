#ifndef __RADIO_H
#define __RADIO_H

#include "Buffer.h"

void lora_start(void (*cb)(const char *buf, unsigned int plen, int rssi));
bool lora_tx(const Buffer& packet);
unsigned long int lora_speed_bps();

#endif
