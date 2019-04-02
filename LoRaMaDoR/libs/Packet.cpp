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

bool Packet::check_callsign(const Buffer &sbuf)
{
	unsigned int length = sbuf.length();
	const char *s = sbuf.cold();

	if (length < 2) {
		return false;
	} else if (length == 2) {
		char c0 = s[0];
		char c1 = s[1];
		if (c0 != 'Q') {
			return false;
		}
		if (c1 < 'A' || c1 > 'Z') {
			return false;
		}
	} else {
		char c0 = s[0];
		if (c0 == 'Q'|| c0 < 'A' || c0 > 'Z') {
			return false;
		}

		const char *ssid_delim = strchr(s, '-');
		unsigned int prefix_length;

		if (ssid_delim) {
			const char *ssid = ssid_delim + 1;
			prefix_length = ssid_delim - s;
			int ssid_length = length - 1 - prefix_length;
			if (ssid_length <= 0 || ssid_length > 2) {
				return false;
			}
			bool sig = false;
			for (int i = 0; i < ssid_length; ++i) {
				char c = ssid[i];
				if (c < '0' || c > '9') {
					return false;
				}
				if (c != '0') {
					// found significant digit
					sig = true;
				} else if (! sig) {
					// non-significant 0
					return false;
				}
			}
		} else {
			prefix_length = length;
		}

		if (prefix_length > 7 || prefix_length < 4) {
			return false;
		}
		for (unsigned int i = 1; i < prefix_length; ++i) {
			char c = s[i];
			if (c >= '0' && c <= '9') {
			} else if (c >= 'A' && c <= 'Z') {
			} else {
				return false;
			}
		}
	}

	return true;
}

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

bool Packet::parse_params(const char* data,
			unsigned long int &ident, Params &params)
{
	return parse_params(data, strlen(data), ident, params);
}

bool Packet::parse_params(const char *data, unsigned int len,
		unsigned long int &ident, Params &params)
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

	// valid only if there was an ident among params
	return ident;
}

static bool decode_preamble(const char* data, unsigned int len,
		Buffer &to, Buffer &from, unsigned long int& ident, Params& params)
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

	to = Buffer(data, d1 - data);
	from = Buffer(d1 + 1, d2 - d1 - 1);

	to.uppercase();
	from.uppercase();

	if (!Packet::check_callsign(to) || !Packet::check_callsign(from)) {
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

Packet::Packet(const char* to, const char* from, unsigned long int ident, 
			const Params& params, const Buffer& msg): 
			_to(to), _from(from), _ident(ident), _params(params), _msg(msg)
{
	_sparams = encode_params(_ident, _params);
	_to.uppercase();
	_from.uppercase();

	char scratchpad[32];
	snprintf(scratchpad, 31, "%s:%ld", _from.cold(), _ident);
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

Ptr<Packet> Packet::decode_l2(const char *data, unsigned int len)
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
		return decode_l3(rs_decoded, len - REDUNDANCY);
	} else {
		memcpy(rs_encoded, data, len - REDUNDANCY);
		memcpy(rs_encoded + MSGSIZE_LONG, data + len - REDUNDANCY, REDUNDANCY);
		if (rs_long.Decode(rs_encoded, rs_decoded)) {
			decode_error = 997;
			return 0;
		}
		return decode_l3(rs_decoded, len - REDUNDANCY);
	}
}

// just for testing
Ptr<Packet> Packet::decode_l3(const char* data)
{
	return decode_l3(data, strlen(data));
}

Ptr<Packet> Packet::decode_l3(const char* data, unsigned int len)
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

	Buffer to;
	Buffer from;
	Params params;
	unsigned long int ident = 0;

	if (! decode_preamble(preamble, preamble_len, to, from, ident, params)) {
		return 0;
	}

	return new Packet(to.cold(), from.cold(), ident, params, Buffer(msg, msg_len));
}

Ptr<Packet> Packet::change_msg(const Buffer& msg) const
{
	return new Packet(this->to(), this->from(), this->ident(), this->params(), msg);
}

Ptr<Packet> Packet::change_params(const Params&new_params) const
{
	return new Packet(this->to(), this->from(), this->ident(), new_params, this->msg());
}

bool encode_param(const Buffer& k, const Buffer& v, void* vs)
{
	char scratchpad[251];
	if (! v.str_equal(None)) {
		snprintf(scratchpad, sizeof(scratchpad) - 1, ",%s=%s", k.cold(), v.cold());
	} else {
		snprintf(scratchpad, sizeof(scratchpad) - 1, ",%s", k.cold());
	}
	Buffer *b = (Buffer*) vs;
	b->append(scratchpad, strlen(scratchpad));
	return true; // do not stop foreach
}

Buffer Packet::encode_params(unsigned long int ident, const Params &params)
{
	char sident[20];
	sprintf(sident, "%ld", ident);
	Buffer p(sident);
	params.foreach(&p, &encode_param);
	return p;
}

Buffer Packet::encode_l3() const
{
	unsigned int len = _to.length() + 1 + _from.length() + 1 + _sparams.length() + 1 + _msg.length();
	Buffer b(len);
	char *w = b.hot();

	for (unsigned int i = 0; i < _to.length(); ++i) {
		*w++ = _to.cold()[i];
	}
	*w++ = '<';
	for (unsigned int i = 0; i < _from.length(); ++i) {
		*w++ = _from.cold()[i];
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
	char scratchpad[255];
	snprintf(scratchpad, 254, "pkt %s < %s : %s msg %s",
		_to.cold(), _from.cold(), _sparams.cold(), _msg.cold());
	return Buffer(scratchpad);
}
const char* Packet::to() const
{
	return _to.cold();
}

const char* Packet::from() const
{
	return _from.cold();
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

int Packet::get_decode_error()
{
  return decode_error;
}

