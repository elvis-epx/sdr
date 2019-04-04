// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#ifndef __NETWORK_H
#define __NETWORK_H

#include "Vector.h"
#include "Dict.h"
#include "Packet.h"
#include "Radio.h"
#include "Task.h"

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
	PacketTx(const Buffer& encoded_packet,
		unsigned long int offset,
		TaskCallable* callback_target,
		unsigned long int (TaskCallable::*callback)(Task*)):
			Task(offset, callback_target, callback),
			encoded_packet(encoded_packet) {}
	virtual ~PacketTx() {}
protected:
	virtual unsigned long int run();
private:
	// read by callback tx(), who downcasts Task to PacketTx
	Buffer encoded_packet;
}

// Task who calls back Network::forward() 
class PacketFwd: public Task {
public:
	PacketFwd(const Ptr<Packet> packet,
		int rssi,
		bool we_are_origin,
		unsigned long int offset,
		TaskCallable* callback_target,
		unsigned long int (TaskCallable::*callback)(Task*)):
			Task(offset, callback_target, callback),
			packet(packet), rssi(rssi),
			we_are_origin(we_are_origin) {}
	virtual ~PacketFwd() {}
protected:
	virtual unsigned long int run();
private:
	// read by callback forward(), who downcasts Task to PacketFwd
	int rssi;
	bool we_are_origin;
	const Ptr<Packet> packet;
}

class Network: public TaskCallable {
public:
	Network(const char *callsign);
	virtual ~Network();
	unsigned int get_pkt_id();
	void send(const char *to, const Dict &params, const Buffer& msg);
	void sendmsg(const Ptr<Packet> pkt);
	void recv(Ptr<Packet> pkt);
	void radio_recv(const char *recv_area, unsigned int plen, int rssi);
	unsigned long int beacon(unsigned long int, Task*);
	unsigned long int clean_recv_log(unsigned long int, Task*);
	unsigned long int clean_adjacent_stations(unsigned long int, Task*);
	unsigned long int reset_pkt_id(unsigned long int, Task*);
	unsigned long int tx(unsigned long int, Task*);
	static unsigned long int random(unsigned long int);

private:
	void forward(Task*);

	Buffer my_callsign;
	Dict<RecvLogItem> recv_log;
	Dict<AdjacentStation> adjacent_stations;
	unsigned int last_pkt_id;
	Ptr<TaskManager> task_mgr;
	Vector< Ptr<Modifier> > modifiers;
	Vector< Ptr<Handler> > handlers;
};
