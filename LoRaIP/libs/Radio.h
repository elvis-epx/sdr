#ifndef __RADIO_H
#define __RADIO_H

bool setup_lora();
void loraip_tx(const char *buf, unsigned int len);
void loraip_rx(const char *buf, unsigned int len);
unsigned long int lora_speed_bps();

#endif
