/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "Packet.h"
#include "RS-FEC.h"

static const int MSGSIZE_SHORT = 80;
static const int MSGSIZE_LONG = 180;
static const int REDUNDANCY = 20;

char rs_encoded[MSGSIZE_LONG + REDUNDANCY];
char rs_decoded[MSGSIZE_LONG];

RS::ReedSolomon<MSGSIZE_LONG, REDUNDANCY> rs_long;
RS::ReedSolomon<MSGSIZE_SHORT, REDUNDANCY> rs_short;

static int decode_error;

static bool parse_symbol_param(const char *data, unsigned int len, Buffer& key, Buffer& value)
{
	if (! len) {
		decode_error = 1;
		return false;
	}

	unsigned int skey_len = 0;
	unsigned int svalue_len = 0;

	// find '=' separator, if exists
	const char *equal = (const char*) memchr(data, '=', len);

	if (! equal) {
		// naked key
		skey_len = len;
		svalue_len = 0;
	} else {
		// key=value, value may be empty
		skey_len = equal - data;
		svalue_len = len - skey_len - 1;
	}

	// check key name characters
	for (unsigned int i = 0; i < skey_len; ++i) {
		char c = data[i];
		if (c >= 'a' && c <= 'z') {
		} else if (c >= 'A' && c <= 'Z') {
		} else if (c >= '0' && c <= '9') {
		} else {
			decode_error = 2;
			return false;
		}
	}
	
	// check value characters, if there is a value
	if (equal) {
		for (unsigned int i = 0; i < svalue_len; ++i) {
			char c = equal[1 + i];
			if (strchr("= ,:<", c) || c == 0) {
				decode_error = 3;
				return false;
			}
		}
	}

	key = Buffer(data, skey_len);

	if (equal) {
		value = Buffer(equal + 1, svalue_len);
	} else {
		value = Buffer(None);
	}

	return true;
}

static bool parse_ident_param(const char* s, unsigned int len, unsigned long int &ident)
{
	char *stop;
	ident = strtol(s, &stop, 10);
	if (ident <= 0) {
		decode_error = 4;
		return false;
	}
	if (len != (stop - s)) {
		decode_error = 5;
		return false;
	}

	char n[20];
	// FIXME use Buffer::sprintf
	sprintf(n, "%ld", ident);
	if (strlen(n) != len) {
		decode_error = 6;
		return false;
	}

	return true;
}

static bool parse_param(const char* data, unsigned int len,
		unsigned long int &ident, Buffer &key, Buffer &value)
{
	if (! len) {
		decode_error = 50;
		return false;
	}

	char c = data[0];

	if (c >= '0' && c <= '9') {
		return parse_ident_param(data, len, ident);
	} else if (c >= 'a' && c <= 'z') {
		ident = 0;
		return parse_symbol_param(data, len, key, value);
	} else if (c >= 'A' && c <= 'Z') {
		ident = 0;
		return parse_symbol_param(data, len, key, value);
	}

	decode_error = 7;
	return false;
}

bool Packet::parse_params_cli(const Buffer &data, Params &params)
{
	unsigned long int dummy;
	return parse_params(data.cold(), data.length(), dummy, params, true);
}

bool Packet::parse_params(const char* data,
			unsigned long int &ident, Params &params)
{
	return parse_params(data, strlen(data), ident, params, false);
}

bool Packet::parse_params(const char *data, unsigned int len,
		unsigned long int &ident, Params &params)
{
	return parse_params(data, len, ident, params, false);
}

bool Packet::parse_params(const char *data, unsigned int len,
		unsigned long int &ident, Params &params,
		bool waive_ident)
{
	ident = 0;
	params = Params();

	while (len > 0) {
		unsigned int param_len;
		unsigned int advance_len;

		const char *comma = (const char*) memchr(data, ',', len);
		if (! comma) {
			// last, or only, param
			param_len = len;
			advance_len = len;
		} else {
			param_len = comma - data;
			advance_len = param_len + 1;
		}

		if (! param_len) {
			decode_error = 8;
			return false;
		}

		unsigned long int tident = 0;
		Buffer key;
		Buffer value;

		if (! parse_param(data, param_len, tident, key, value)) {
			return false;
		}
		if (tident) {
			// parameter is ident
			ident = tident;
		} else {
			// parameter is key=value or naked key
			params.put(key, value); // uppers key case for us
		}

		data += advance_len;
		len -= advance_len;
	}

	return ident || waive_ident;
}

static bool decode_preamble(const char* data, unsigned int len,
		Callsign &to, Callsign &from, unsigned long int& ident, Params& params)
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
	if (! Packet::parse_params(sparams, sparams_len, ident, params)) {
		return false;
	}

	return true;
}

Packet::Packet(const Callsign &to, const Callsign &from, unsigned long int ident, 
			const Params& params, const Buffer& msg, int rssi): 
			_to(to), _from(from), _ident(ident), _params(params), _msg(msg), _rssi(rssi)
{
	_sparams = encode_params(_ident, _params);

	// FIXME use Buffer::sprintf
	char scratchpad[32];
	snprintf(scratchpad, 31, "%s:%ld", _from.buf().cold(), _ident);
	_signature = Buffer(scratchpad);
}

Packet::Packet(Packet &&model): _to(model._to), _from(model._from),
		_ident(model._ident),
		_params(model._params),
		_sparams(model._sparams),
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
		return 0;
	}

	memset(rs_encoded, 0, sizeof(rs_encoded));
	if (len <= (MSGSIZE_SHORT + REDUNDANCY)) {
		memcpy(rs_encoded, data, len - REDUNDANCY);
		memcpy(rs_encoded + MSGSIZE_SHORT, data + len - REDUNDANCY, REDUNDANCY);
		if (rs_short.Decode(rs_encoded, rs_decoded)) {
			decode_error = 998;
			return 0;
		}
		return decode_l3(rs_decoded, len - REDUNDANCY, rssi);
	} else {
		memcpy(rs_encoded, data, len - REDUNDANCY);
		memcpy(rs_encoded + MSGSIZE_LONG, data + len - REDUNDANCY, REDUNDANCY);
		if (rs_long.Decode(rs_encoded, rs_decoded)) {
			decode_error = 997;
			return 0;
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
	unsigned long int ident = 0;

	if (! decode_preamble(preamble, preamble_len, to, from, ident, params)) {
		return 0;
	}

	return new Packet(to, from, ident, params, Buffer(msg, msg_len), rssi);
}

Ptr<Packet> Packet::change_msg(const Buffer& msg) const
{
	return new Packet(this->to(), this->from(), this->ident(), this->params(), msg);
}

Ptr<Packet> Packet::change_params(const Params&new_params) const
{
	return new Packet(this->to(), this->from(), this->ident(), new_params, this->msg());
}

Buffer Packet::encode_params(unsigned long int ident, const Params &params)
{
	// FIXME use Buffer::sprintf
	char scratchpad[255];
	snprintf(scratchpad, sizeof(scratchpad) - 1, "%ld", ident);
	Buffer buf(scratchpad);

	const Vector<Buffer>& keys = params.keys();
	for (unsigned int i = 0; i < keys.size(); ++i) {
		const Buffer& key = keys[i];
		const Buffer& value = params[key];
		if (! value.str_equal(None)) {
			snprintf(scratchpad, sizeof(scratchpad) - 1, ",%s=%s",
				key.cold(), value.cold());
		} else {
			snprintf(scratchpad, sizeof(scratchpad) - 1, ",%s",
				key.cold());
		}
		buf.append(scratchpad, strlen(scratchpad));
	}

	return buf;
}

Buffer Packet::encode_l3() const
{
	// FIXME use higher-level Buffer functions
	unsigned int len = _to.buf().length() + 1 + _from.buf().length() + 1 + _sparams.length() + 1 + _msg.length();
	Buffer b(len);
	char *w = b.hot();

	for (unsigned int i = 0; i < _to.buf().length(); ++i) {
		*w++ = _to.buf().cold()[i];
	}
	*w++ = '<';
	for (unsigned int i = 0; i < _from.buf().length(); ++i) {
		*w++ = _from.buf().cold()[i];
	}
	*w++ = ':';
	for (unsigned int i = 0; i < _sparams.length(); ++i) {
		*w++ = _sparams.cold()[i];
	}
	*w++ = ' ';
	memcpy(w, _msg.cold(), _msg.length());

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
	// FIXME use Buffer::sprintf
	char scratchpad[255];
	snprintf(scratchpad, 254, "pkt %s < %s : %s msg %s",
		_to.buf().cold(), _from.buf().cold(), _sparams.cold(), _msg.cold());
	return Buffer(scratchpad);
}
Callsign Packet::to() const
{
	return _to;
}

Callsign Packet::from() const
{
	return _from;
}

const char* Packet::sparams() const
{
  return _sparams.cold();
}

unsigned long int Packet::ident() const
{
	return _ident;
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

