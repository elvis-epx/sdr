// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#ifndef __NETWORK_H
#define __NETWORK_H

#include "Utility.h"
#include "Packet.h"
#include "Scheduler.h"
#include "Radio.h"

class Beacon: public Scheduled {
public:
	Beacon(const Network* net);
	virtual bool call();
};

class CleanRecvLog: public Scheduled {
	CleanRecvLog(const Network* net);
	virtual bool call();
};

class CleanAdjacents: public Scheduled {
	CleanAdjacents(const Network* net);
	virtual bool call();
};

struct AdjacentStation {
	long int last_q;
};

struct RecvLogItem {
	int rssi;
	long int timestamp;
}

class Network {
public:
	Network(const char *callsign);
	void clean_adjacent_stations();
	void clean_recv_log();
	unsigned int get_pkt_id();
	void send(const char *to, const Dict &params, const Buffer& msg);
	void sendmsg(Packet *pkt);
	void recv(Packet *pkt);
	void radio_recv(Packet *pkt, int radio_rssi);

private:
	void forward(int radio_rssi, const Packet *pkt, bool we_are_origin);

	Buffer my_prefix;

	ODict<RecvLogItem> recv_log;
	Scheduled *clean_recv_log;

	ODict<AdjacentStation> adjacent_stations;
	Scheduled *clean_adjacent_stations;

	Scheduled *beacon;

	unsigned int last_pkt_id;
	Scheduled *reset_pkt_id;

	// FIXME array of Scheduled* to send individual packets
