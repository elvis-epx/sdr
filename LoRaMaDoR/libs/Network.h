// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#ifndef __NETWORK_H
#define __NETWORK_H

#include "Utility.h"
#include "Packet.h"
#include "Task.h"
#include "Radio.h"
#include "Dict.h"

struct AdjacentStation {
	long int last_q;
};

struct RecvLogItem {
	int rssi;
	long int timestamp;
}

// Task who calls back Network::tx_task() 
class PacketTx: public Task {
public:
	PacketTx(const Buffer& packet,
		unsigned long int offset,
		TaskCallable* cb_target,
		unsigned long int (TaskCallable::*callback)(Task*));
	virtual bool run();
	virtual ~Task();

	// read by tx_task() 
	Buffer packet;
}

class Network: public TaskCallable {
public:
	Network(const char *callsign);
	virtual ~Network() {};
	void clean_adjacent_stations();
	void clean_recv_log();
	unsigned int get_pkt_id();
	void send(const char *to, const Dict &params, const Buffer& msg);
	void sendmsg(Packet *pkt);
	void recv(Packet *pkt);
	void radio_recv(Packet *pkt, int radio_rssi);
	unsigned long int beacon(Task*);
	unsigned long int clean_recv_log(Task*);
	unsigned long int clean_adjacent_stations(Task*);
	unsigned long int reset_pkt_id(Task*);
	unsigned long int tx(Task*);

private:
	void forward(int radio_rssi, const Packet *pkt, bool we_are_origin);

	Buffer my_prefix;
	Dict<RecvLogItem> recv_log;
	Dict<AdjacentStation> adjacent_stations;
	unsigned int last_pkt_id;
	Ptr<TaskManager> task_mgr;
};
