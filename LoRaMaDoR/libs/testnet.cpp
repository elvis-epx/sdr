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

	while (1) {
		unsigned long int to = net()->task_mgr->next_task() + 1;

		fd_set set;
		struct timeval timeout;
		FD_ZERO (&set);
		FD_SET (s, &set);
		timeout.tv_sec = to / 1000;
		timeout.tv_usec = (to % 1000) * 1000;

		int sel = select(FD_SETSIZE, &set, NULL, NULL, &timeout);
		if (sel < 0) {
			printf("select() failure\n");
			return 1;
		}

		if (FD_ISSET(s, &set)) {
			_lora_rx();
		}
		net()->task_mgr->run(arduino_millis());
	}
}
