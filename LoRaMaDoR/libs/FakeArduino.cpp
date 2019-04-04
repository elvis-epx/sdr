#include <sys/time.h>
#include <stdlib.h>
#include "Buffer.h"

static struct timeval tm_first;
static bool virgin = true;

unsigned long int arduino_millis()
{
	if (virgin) {
		gettimeofday(&tm_first, 0);
		virgin = false;
	}
	struct timeval tm;
	gettimeofday(&tm, 0);
	return ((tm.tv_sec * 1000000 + tm.tv_usec)
		- (tm_first.tv_sec * 1000000 + tm_first.tv_usec)) / 1000;
}

long int arduino_random(long int min, long int max)
{
	return min + random() % (max - min + 1);
}

void setup_lora()
{
}

unsigned long int lora_speed_bps()
{
	return 1200;
}

void lora_tx(const Buffer&)
{
	// FIXME print, impl
}

void lora_rx(void (*)(char const*, unsigned int, int))
{
	// FIXME impl 
}
