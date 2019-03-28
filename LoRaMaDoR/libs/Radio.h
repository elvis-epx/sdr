#include "Utility.h"

bool setup_lora_ttgo();
bool setup_lora_32u4();
void lora_rx(void (*cb)(const char *buf, unsigned int plen, int rssi));
int lora_tx(const Buffer& packet);
