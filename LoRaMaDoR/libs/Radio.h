#include "Buffer.h"

bool setup_lora();
void lora_rx(void (*cb)(const char *buf, unsigned int plen, int rssi));
int lora_tx(const Buffer& packet);
unsigned long int speed_bps();
