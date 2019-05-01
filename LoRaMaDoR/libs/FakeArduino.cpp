// Emulation of certain Arduino APIs for testing on UNIX

#include <sys/time.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include "Buffer.h"

// Emulation of millis() and random()

static struct timeval tm_first;
static bool virgin = true;

unsigned long int arduino_millis()
{
	if (virgin) {
		gettimeofday(&tm_first, 0);
		virgin = false;
		srandom(tm_first.tv_sec + tm_first.tv_usec);
	}
	struct timeval tm;
	gettimeofday(&tm, 0);
	return ((tm.tv_sec * 1000000 + tm.tv_usec)
		- (tm_first.tv_sec * 1000000 + tm_first.tv_usec)) / 1000 + 1;
}

long int arduino_random(long int min, long int max)
{
	if (virgin) {
		gettimeofday(&tm_first, 0);
		virgin = false;
		srandom(tm_first.tv_sec + tm_first.tv_usec);
	}
	return min + random() % (max - min + 1);
}

// Logging

void logs(const char* s1, const char* s2)
{
	printf("%s %s\n", s1, s2);
}

void logi(const char* s1, long int s2)
{
	printf("%s %ld\n", s1, s2);
}

// Emulation of LoRa APIs, network and radio

#define PORT 6000
#define GROUP "239.0.0.1"

static int sock = -1;

int lora_emu_socket()
{
	return sock;
}

void setup_lora()
{
	// from https://web.cs.wpi.edu/~claypool/courses/4514-B99/samples/multicast.c
	struct ip_mreq mreq;

	sock = socket(AF_INET, SOCK_DGRAM, 0);
	if (sock < 0) {
		perror("socket");
		exit(1);
	}

	// Disable receiving our own multicast packets
	int loop = 0;
	setsockopt(sock, IPPROTO_IP, IP_MULTICAST_LOOP, &loop, sizeof(loop));

	// Allow multiple listeners to the same port
	int optval = 1;
	setsockopt(sock, SOL_SOCKET, SO_REUSEPORT, &optval, sizeof(optval));

	// Enter multicast group
	mreq.imr_multiaddr.s_addr = inet_addr(GROUP);
	mreq.imr_interface.s_addr = htonl(INADDR_ANY);
	if (setsockopt(sock, IPPROTO_IP, IP_ADD_MEMBERSHIP,
					&mreq, sizeof(mreq)) < 0) {
		perror("setsockopt mreq");
		exit(1);
	}

	// listen UDP port
	struct sockaddr_in addr;
	memset((char *)&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = htonl(INADDR_ANY);
	addr.sin_port = htons(PORT);

	if (bind(sock, (struct sockaddr *) &addr, sizeof(addr)) < 0) {
		perror("bind");
		exit(1);
	}
}

unsigned long int lora_speed_bps()
{
	return 1200;
}

bool lora_tx_async(const Buffer& b)
{
	// Send to multicast group & port
	struct sockaddr_in addr;
	memset((char *)&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = inet_addr(GROUP);
	addr.sin_port = htons(PORT);

	int sent = sendto(sock, b.cold(), b.length(), 0, (struct sockaddr *) &addr, sizeof(addr));
	if (sent < 0) {
		perror("sendto");
		exit(1);
	}
	printf("Sent packet\n");
	return true;
}

bool lora_tx_busy()
{
	return false;
}

static void (*rx_callback)(char const*, unsigned int, int) = 0;

void lora_rx(void (*new_cb)(char const*, unsigned int, int))
{
	rx_callback = new_cb;
}

void _lora_rx()
{
	char message[256];
	struct sockaddr_in from;
	socklen_t fromlen = sizeof(from);
	int rec = recvfrom(sock, message, sizeof(message), 0, (struct sockaddr *) &from, &fromlen);
	if (rec < 0) {
		perror("recvfrom");
		exit(1);
	}
	printf("Received packet\n");
	rx_callback(message, rec, -50);
}
