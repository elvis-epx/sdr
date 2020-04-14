#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "Radio.h"

extern char testbuf[255];
extern unsigned int testbuflen;
extern void _on_receive(int plen);

void loraip_rx(char const* pkt, unsigned int len)
{
	printf("rx data %s len %d\n", pkt, len);
}

int main()
{
	loraip_tx("abcde", 5);
	assert(testbuf[4] == 'e');
	assert(testbuflen == 25);
	_on_receive(25);
	testbuf[0] = '#';
	testbuf[1] = '#';
	testbuf[2] = '#';
	testbuf[3] = '#';
	testbuf[4] = '#';
	_on_receive(25);
	testbuf[5] = '#';
	testbuf[6] = '#';
	testbuf[7] = '#';
	testbuf[8] = '#';
	testbuf[9] = '#';
	testbuf[10] = '#';
	_on_receive(25);
	printf("Autotest ok\n");
}
