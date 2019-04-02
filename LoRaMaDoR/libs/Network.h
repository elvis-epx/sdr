// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#ifndef __NETWORK_H
#define __NETWORK_H

#include "Utility.h"
#include "Packet.h"
#include "Task.h"
#include "Radio.h"
#include "ODict.h"

struct AdjacentStation {
	long int last_q;
};

struct RecvLogItem {
	int rssi;
	long int timestamp;
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
	bool beacon(const char*);
	bool clean_recv_log(const char*);
	bool clean_adjacent_stations(const char*);
	bool reset_pkt_id(const char*);
	bool tx_task(const char *);

private:
	void forward(int radio_rssi, const Packet *pkt, bool we_are_origin);

	Buffer my_prefix;
	ODict<RecvLogItem> recv_log;
	ODict<AdjacentStation> adjacent_stations;
	unsigned int last_pkt_id;
	Task* fixed_tasks[];
	Task* oneoff_tasks[];
};
