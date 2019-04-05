#ifndef __RADIO_H
#define __RADIO_H

#include "Buffer.h"

bool setup_lora();
void lora_rx(void (*cb)(const char *buf, unsigned int plen, int rssi));
int lora_tx(const Buffer& packet);
unsigned long int lora_speed_bps();

// async tx protocol
// 1) lora_tx_async().
//    If returns false, try again later (but should not happen)
// 2) Busy status.
//    keep calling lora_tx_busy() until it returns false.
//    (RX is reactivated when it first returns false.)
// 3) do not call lora_tx_async() while state is busy.

int lora_tx_async(const Buffer& packet);
bool lora_tx_busy();

#endif
