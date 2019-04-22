#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include "Network.h"
#include "ArduinoBridge.h"

// Radio emulation hooks in FakeArduino.cpp
int lora_emu_socket();
void _lora_rx();

int main(int argc, char* argv[])
{
	if (argc < 2) {
		printf("Specify a callsign\n");
		return 1;
	}
	config_net(argv[1]);

	// Main loop simulation (in Arduino, would be a busy loop)
	int s = lora_emu_socket();
	printf("Socket %d\n", s);

	while (1) {
		unsigned long int now = arduino_millis();
		unsigned long int toa = net()->task_mgr.next_task();
		unsigned long int to = toa - now;

		fd_set set;
		FD_ZERO(&set);
		FD_SET(s, &set);

		struct timeval timeout;
		struct timeval* ptimeout = 0;
		if (to > 0) {
			printf("Timeout: %lu\n", to);
			timeout.tv_sec = to / 1000;
			timeout.tv_usec = (to % 1000) * 1000;
			ptimeout = &timeout;
		} else {
			printf("No timeout (bug?)\n");
		}

		int sel = select(s + 1, &set, NULL, NULL, ptimeout);
		if (sel < 0) {
			perror("select() failure");
			return 1;
		}

		if (FD_ISSET(s, &set)) {
			_lora_rx();
		} else {
			net()->task_mgr.run(arduino_millis());
		}
	}
}
