// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#ifndef __NETWORK_H
#define __NETWORK_H

#include "Vector.h"
#include "Dict.h"
#include "Packet.h"
#include "Modifier.h"
#include "Handler.h"
#include "Radio.h"
#include "Task.h"

struct AdjacentStation {
	AdjacentStation(int rssi, unsigned long int timestamp):
		rssi(rssi), timestamp(timestamp) {}
	AdjacentStation() {}
	int rssi;
	unsigned long int timestamp;
};

struct RecvLogItem {
	RecvLogItem(int rssi, unsigned long int timestamp):
		rssi(rssi), timestamp(timestamp) {}
	RecvLogItem() {}
	int rssi;
	unsigned long int timestamp;
};

class Network: public TaskCallable {
public:
	Network(const char *callsign); // client must get the singleton instead
	virtual ~Network();
	unsigned int get_pkt_id();
	void send(const char *to, const Params &params, const Buffer& msg);
	void recv(Ptr<Packet> pkt);
	static unsigned long int fudge(unsigned long int, double fudge);
	void radio_recv(const char *recv_area, unsigned int plen, int rssi);
	virtual unsigned long int task_callback(int, unsigned long int, Task*);

private:
	void sendmsg(const Ptr<Packet> pkt);
	unsigned long int forward(unsigned long int, Task*);
	unsigned long int clean_recv_log(unsigned long int, Task*);
	unsigned long int clean_adjacent_stations(unsigned long int, Task*);
	unsigned long int beacon(unsigned long int, Task*);
	unsigned long int tx(unsigned long int, Task*);
	unsigned long int reset_pkt_id(unsigned long int, Task*);

	Buffer my_callsign;
	Dict<RecvLogItem> recv_log;
	Dict<AdjacentStation> adjacent_stations;
	unsigned int last_pkt_id;
	Ptr<TaskManager> task_mgr;
	Vector< Ptr<Modifier> > modifiers;
	Vector< Ptr<Handler> > handlers;
};

void config_net(const char *callsign);
Ptr<Network> net(); // returns singleton

#endif
