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
void lora_emu_rx();

int main(int argc, char* argv[])
{
	if (argc < 2) {
		printf("Specify a callsign\n");
		return 1;
	}

	Callsign cs(argv[1]);
	if (!cs.is_valid()) {
		printf("Callsign invalid.\n");
		return 2;
	}
	Ptr<Network> the_net(new Network(cs));

	// Main loop simulation (in Arduino, would be a busy loop)
	int s = lora_emu_socket();
	printf("Socket %d\n", s);

	int x = 5000;
	while (x-- > 0) {
		Ptr<Task> tsk = the_net->task_mgr.next_task();

		fd_set set;
		FD_ZERO(&set);
		FD_SET(s, &set);

		struct timeval timeout;
		struct timeval* ptimeout = 0;
		if (tsk) {
			long int now = arduino_millis();
			long int to = tsk->next_run() - now;
			printf("Timeout: %s %ld\n", tsk->get_name(), to);
			if (to < 0) {
				to = 0;
			}
			timeout.tv_sec = to / 1000;
			timeout.tv_usec = (to % 1000) * 1000;
			ptimeout = &timeout;
		} else {
			printf("No timeout (bug?)\n");
			timeout.tv_sec = 1;
			timeout.tv_usec = 0;
		}
		ptimeout = &timeout;

		int sel = select(s + 1, &set, NULL, NULL, ptimeout);
		if (sel < 0) {
			perror("select() failure");
			return 1;
		}

		if (FD_ISSET(s, &set)) {
			lora_emu_rx();
		} else {
			the_net->run_tasks(arduino_millis());
		}
	}
}
