/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifndef __PACKET_H
#define  __PACKET_H

#include "Vector.h"
#include "Buffer.h"
#include "Pointer.h"
#include "Callsign.h"
#include "Params.h"

struct Packet {
	Packet(const Callsign &to, const Callsign &from, 
		const Params& params, const Buffer& msg, int rssi=0);
	~Packet();

	static Ptr<Packet> decode_l2(const char* data, unsigned int len, int rssi);
	static int get_decode_error();

	/* public for unit testing */
	static Ptr<Packet> decode_l3(const char* data, unsigned int len, int rssi);
	static Ptr<Packet> decode_l3(const char *data);

	Packet(const Packet &) = delete;
	Packet(Packet &&);
	Packet() = delete;
	Packet& operator=(const Packet &) = delete;
	bool operator==(const Packet &) = delete;

	Ptr<Packet> change_msg(const Buffer&) const;
	Ptr<Packet> change_params(const Params&) const;
	Buffer encode_l2() const;

	/* public for unit testing */
	Buffer encode_l3() const;

	bool is_dup(const Packet& other) const;
	Buffer repr() const;
	const char *signature() const;
	Callsign to() const;
	Callsign from() const;
	const Params& params() const;
	const Buffer& msg() const;
	int rssi() const;

private:
	Callsign _to;
	Callsign _from;
	const Params _params;
	Buffer _signature;
	const Buffer _msg;
	int _rssi;
};

#endif
