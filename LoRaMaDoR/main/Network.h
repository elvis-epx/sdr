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

class Network: public TaskCallable
{
public:
	Network(const Callsign &callsign);
	virtual ~Network();

	void send(const Callsign &to, Params params, const Buffer& msg);
	void run_tasks(unsigned long int);

	// publicised to bridge with uncoupled code
	void radio_recv(const char *recv_area, unsigned int plen, int rssi);
	virtual unsigned long int task_callback(int, unsigned long int, Task*);
	unsigned int get_last_pkt_id() const;
	unsigned int get_next_pkt_id();
	Callsign me() const;

	// publicised for testing purposes
	TaskManager task_mgr;

private:
	void recv(Ptr<Packet> pkt);
	void sendmsg(const Ptr<Packet> pkt);
	unsigned long int forward(unsigned long int, Task*);
	unsigned long int clean_recv_log(unsigned long int, Task*);
	unsigned long int clean_adjacent_stations(unsigned long int, Task*);
	unsigned long int beacon(unsigned long int, Task*);
	unsigned long int tx(unsigned long int, Task*);

	Callsign my_callsign;
	Dict<RecvLogItem> recv_log;
	Dict<AdjacentStation> adjacent_stations;
	unsigned int last_pkt_id;
	Vector< Ptr<Modifier> > modifiers;
	Vector< Ptr<Handler> > handlers;

};

#endif
