/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "Packet.h"
#include "Params.h"
#include "RS-FEC.h"

static const int MSGSIZE_SHORT = 80;
static const int MSGSIZE_LONG = 180;
static const int REDUNDANCY = 20;

char rs_encoded[MSGSIZE_LONG + REDUNDANCY];
char rs_decoded[MSGSIZE_LONG];

RS::ReedSolomon<MSGSIZE_LONG, REDUNDANCY> rs_long;
RS::ReedSolomon<MSGSIZE_SHORT, REDUNDANCY> rs_short;

static int decode_error;

static bool decode_preamble(const char* data, unsigned int len,
		Callsign &to, Callsign &from, Params& params)
{
	const char *d1 = (const char*) memchr(data, '<', len);
	const char *d2 = (const char*) memchr(data, ':', len);

	if (d1 == 0 || d2 == 0) {
		decode_error = 100;
		return false;
	} else if (d1 >= d2)  {
		decode_error = 101;
		return false;
	} else if ((d2 - data) >= len) {
		decode_error = 102;
		return false;
	} else if (d1 == data) {
		decode_error = 103;
		return false;
	}

	to = Callsign(Buffer(data, d1 - data));
	from = Callsign(Buffer(d1 + 1, d2 - d1 - 1));

	if (!to.is_valid() || !from.is_valid()) {
		decode_error = 104;
		return false;
	}

	const char *sparams = d2 + 1;
	unsigned int sparams_len = len - (d2 - data) - 1;
	params = Params(Buffer(sparams, sparams_len));

	if (! params.is_valid_with_ident()) {
		decode_error = 105;
		return false;
	}

	return true;
}

Packet::Packet(const Callsign &to, const Callsign &from,
			const Params& params, const Buffer& msg, int rssi): 
			_to(to), _from(from), _params(params), _msg(msg), _rssi(rssi)
{
	_signature = Buffer::sprintf("%s:%ld", _from.buf().cold(), params.ident());
}

Packet::Packet(Packet &&model): _to(model._to), _from(model._from),
		_params(model._params),
		_msg(model._msg)
{
}

Packet::~Packet()
{
}

Ptr<Packet> Packet::decode_l2(const char *data, unsigned int len, int rssi)
{
	decode_error = 0;
	if (len <= REDUNDANCY || len > (MSGSIZE_LONG + REDUNDANCY)) {
		decode_error = 999;
		return Ptr<Packet>(0);
	}

	memset(rs_encoded, 0, sizeof(rs_encoded));
	if (len <= (MSGSIZE_SHORT + REDUNDANCY)) {
		memcpy(rs_encoded, data, len - REDUNDANCY);
		memcpy(rs_encoded + MSGSIZE_SHORT, data + len - REDUNDANCY, REDUNDANCY);
		if (rs_short.Decode(rs_encoded, rs_decoded)) {
			decode_error = 998;
			return Ptr<Packet>(0);
		}
		return decode_l3(rs_decoded, len - REDUNDANCY, rssi);
	} else {
		memcpy(rs_encoded, data, len - REDUNDANCY);
		memcpy(rs_encoded + MSGSIZE_LONG, data + len - REDUNDANCY, REDUNDANCY);
		if (rs_long.Decode(rs_encoded, rs_decoded)) {
			decode_error = 997;
			return Ptr<Packet>(0);
		}
		return decode_l3(rs_decoded, len - REDUNDANCY, rssi);
	}
}

// just for testing
Ptr<Packet> Packet::decode_l3(const char* data)
{
	return decode_l3(data, strlen(data), -50);
}

Ptr<Packet> Packet::decode_l3(const char* data, unsigned int len, int rssi)
{
	const char *preamble = 0;
	const char *msg = 0;
	unsigned int preamble_len = 0;
	unsigned int msg_len = 0;

	const char *msgd = (const char*) memchr(data, ' ', len);
	
	if (msgd) {
		preamble = data;
		preamble_len = msgd - data;
		msg = msgd + 1;
		msg_len = len - preamble_len - 1;
	} else {
		// valid packet with no message
		preamble = data;
		preamble_len = len;
	}

	Callsign to;
	Callsign from;
	Params params;

	if (! decode_preamble(preamble, preamble_len, to, from, params)) {
		return Ptr<Packet>(0);
	}

	return Ptr<Packet>(new Packet(to, from, params, Buffer(msg, msg_len), rssi));
}

Ptr<Packet> Packet::change_msg(const Buffer& msg) const
{
	return Ptr<Packet>(new Packet(this->to(), this->from(), this->params(), msg));
}

Ptr<Packet> Packet::change_params(const Params&new_params) const
{
	return Ptr<Packet>(new Packet(this->to(), this->from(), new_params, this->msg()));
}

Buffer Packet::encode_l3() const
{
	Buffer b(_to.buf());

	b.append('<');
	b.append_str(_from.buf());
	b.append(':');
	b.append_str(_params.serialized());
	b.append(' ');
	b.append_str(_msg);

	return b;
}

Buffer Packet::encode_l2() const
{
	Buffer b = encode_l3();

	memset(rs_decoded, 0, sizeof(rs_decoded));
	memcpy(rs_decoded, b.cold(), b.length());
	if (b.length() <= MSGSIZE_SHORT) {
		rs_short.Encode(rs_decoded, rs_encoded);
		b.append(rs_encoded + MSGSIZE_SHORT, REDUNDANCY);
	} else {
		rs_long.Encode(rs_decoded, rs_encoded);
		b.append(rs_encoded + MSGSIZE_LONG, REDUNDANCY);
	}

	return b;
}

const char* Packet::signature() const
{
	return _signature.cold();
}

bool Packet::is_dup(const Packet& other) const
{
	return strcmp(this->signature(), other.signature()) == 0;
}

Buffer Packet::repr() const
{
	return Buffer::sprintf("pkt %s < %s : %s msg %s",
				_to.buf().cold(), _from.buf().cold(),
				_params.serialized().cold(), _msg.cold());
}

Callsign Packet::to() const
{
	return _to;
}

Callsign Packet::from() const
{
	return _from;
}

const Params& Packet::params() const
{
	return _params;
}

const Buffer& Packet::msg() const
{
	return _msg;
}

int Packet::rssi() const
{
	return _rssi;
}

int Packet::get_decode_error()
{
	return decode_error;
}

