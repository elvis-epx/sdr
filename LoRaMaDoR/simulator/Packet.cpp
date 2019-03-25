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

RS::ReedSolomon<MSGSIZE_SHORT, REDUNDANCY> rs_short;
#ifndef __AVR__
char rs_encoded[MSGSIZE_LONG + REDUNDANCY];
char rs_decoded[MSGSIZE_LONG];
RS::ReedSolomon<MSGSIZE_LONG, REDUNDANCY> rs_long;
#else
char rs_encoded[MSGSIZE_SHORT + REDUNDANCY];
char rs_decoded[MSGSIZE_SHORT];
#endif

bool Packet::check_callsign(const Buffer &sbuf)
{
	unsigned int length = sbuf.length();
	const char *s = sbuf.rbuf();

	if (length < 2) {
		printf("callsign length < 2\n");
		return false;
	} else if (length == 2) {
		char c0 = s[0];
		char c1 = s[1];
		if (c0 != 'Q') {
			printf("callsign length = 2 and not Q\n");
			return false;
		}
		if (c1 < 'A' || c1 > 'Z') {
			printf("callsign c1 not alpha\n");
			return false;
		}
	} else {
		char c0 = s[0];
		if (c0 == 'Q'|| c0 < 'A' || c0 > 'Z') {
			printf("callsign begins with Q or non-alpha\n");
			return false;
		}

		const char *ssid_delim = strchr(s, '-');
		unsigned int prefix_length;

		if (ssid_delim) {
			const char *ssid = ssid_delim + 1;
			prefix_length = ssid_delim - s;
			int ssid_length = length - 1 - prefix_length;
			if (ssid_length <= 0 || ssid_length > 2) {
				printf("SSID too big %d\n", ssid_length);
				return false;
			}
			bool sig = false;
			for (int i = 0; i < ssid_length; ++i) {
				char c = ssid[i];
				if (c < '0' || c > '9') {
					printf("SSID with non-digit\n");
					return false;
				}
				if (c != '0') {
					// found significant digit
					sig = true;
				} else if (! sig) {
					// non-significant 0
					printf("SSID with non-significant 0\n");
					return false;
				}
			}
		} else {
			prefix_length = length;
		}

		if (prefix_length > 7 || prefix_length < 4) {
			printf("bad prefix size\n");
			return false;
		}
		for (unsigned int i = 1; i < prefix_length; ++i) {
			char c = s[i];
			if (c >= '0' && c <= '9') {
			} else if (c >= 'A' && c <= 'Z') {
			} else {
				printf("bad prefix char\n");
				return false;
			}
		}
	}

	return true;
}

static bool parse_symbol_param(const char *data, unsigned int len, Buffer& key, Buffer*& value)
{
	if (! len) {
		printf("null symbol param length\n");
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
			printf("bad param key name char %c\n", c);
			return false;
		}
	}
	
	// check value characters, if there is a value
	if (equal) {
		for (unsigned int i = 0; i < svalue_len; ++i) {
			char c = equal[1 + i];
			if (strchr("= ,:<", c) || c == 0) {
				printf("param name has invalid char\n");
				return false;
			}
		}
	}

	key = Buffer(data, skey_len);

	if (equal) {
		value = new Buffer(equal + 1, svalue_len);
	} else {
		value = 0;
	}

	return true;
}

static bool parse_ident_param(const char* s, unsigned int len, unsigned long int &ident)
{
	char *stop;
	ident = strtol(s, &stop, 10);
	if (ident <= 0) {
		printf("bad ident value\n");
		return false;
	}
	if (len != (stop - s)) {
		printf("bad ident value len=%u used=%ld\n", len, (stop - s));
		return false;
	}

	char n[20];
	sprintf(n, "%ld", ident);
	if (strlen(n) != len) {
		printf("bad ident value olen=%u nlen=%ld\n", len, strlen(n));
		return false;
	}

	return true;
}

static bool parse_param(const char* data, unsigned int len,
		unsigned long int &ident, Buffer &key, Buffer *&value)
{
	if (! len) {
		printf("param with length 0 \n");
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

	printf("param with bad first character '%s'\n", data);
	return false;
}

bool Packet::parse_params(const char* data,
			unsigned long int &ident, Dict &params)
{
	return parse_params(data, strlen(data), ident, params);
}

bool Packet::parse_params(const char *data, unsigned int len,
		unsigned long int &ident, Dict &params)
{
	ident = 0;
	params = Dict();

	while (len > 0) {
		printf("parsing parameter, remaining len=%u data='%s'\n", len, data);
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
			printf("param data with no len\n");
			return false;
		}

		unsigned long int tident = 0;
		Buffer key;
		Buffer *value = 0;

		if (! parse_param(data, param_len, tident, key, value)) {
			delete value;
			printf("could not parse param in '%s'\n", data);
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
		Buffer &to, Buffer &from, unsigned long int& ident, Dict& params)
{
	const char *d1 = (const char*) memchr(data, '<', len);
	const char *d2 = (const char*) memchr(data, ':', len);

	if (d1 == 0 || d2 == 0) {
		printf("delimiters not found in preamble %s\n", data);
		return false;
	} else if (d1 >= d2)  {
		printf("delimiters swapped or null second section %s\n", data);
		return false;
	} else if ((d2 - data) >= len) {
		printf("empty third section in %s\n", data);
		return false;
	} else if (d1 == data) {
		printf("empty first section in %s\n", data);
		return false;
	}

	to = Buffer(data, d1 - data);
	printf("parsed to: %s\n", to.rbuf());
	from = Buffer(d1 + 1, d2 - d1 - 1);
	printf("parsed from: %s\n", from.rbuf());

	to.uppercase();
	from.uppercase();

	if (!Packet::check_callsign(to) || !Packet::check_callsign(from)) {
		printf("bad callsign in packet\n");
		return false;
	}

	const char *sparams = d2 + 1;
	unsigned int sparams_len = len - (d2 - data) - 1;
	if (! Packet::parse_params(sparams, sparams_len, ident, params)) {
		printf("bad param/params in packet\n");
		return false;
	}

	return true;
}

Packet::Packet(const char* to, const char* from, unsigned long int ident, 
			const Dict& params, const Buffer& msg): 
			_to(to), _from(from), _ident(ident), _params(params), _msg(msg)
{
	_sparams = encode_params(_ident, _params);
	_to.uppercase();
	_from.uppercase();

	char scratchpad[32];
	snprintf(scratchpad, 31, "%s:%ld", _from.rbuf(), _ident);
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

Packet* Packet::decode_l2(const char *data, unsigned int len)
{
	if (len <= REDUNDANCY || len > (MSGSIZE_LONG + REDUNDANCY)) {
		return 0;
	}

	memset(rs_encoded, 0, sizeof(rs_encoded));
	if (len <= (MSGSIZE_SHORT + REDUNDANCY)) {
		memcpy(rs_encoded, data, len - REDUNDANCY);
		memcpy(rs_encoded + MSGSIZE_SHORT, data + len - REDUNDANCY, REDUNDANCY);
		if (rs_short.Decode(rs_encoded, rs_decoded)) {
			printf("RS FEC failed to correct all errors\n");
			return 0;
		}
		return decode_l3(rs_decoded, len - 20);
	} else {
#ifdef __AVR__
		return 0;
#else
		memcpy(rs_encoded, data, len - REDUNDANCY);
		memcpy(rs_encoded + MSGSIZE_LONG, data + len - REDUNDANCY, REDUNDANCY);
		if (rs_long.Decode(rs_encoded, rs_decoded)) {
			printf("RS FEC failed to correct all errors\n");
			return 0;
		}
		return decode_l3(rs_decoded, len - 20);
#endif
	}
}

// just for testing
Packet* Packet::decode_l3(const char* data)
{
	return decode_l3(data, strlen(data));
}

Packet* Packet::decode_l3(const char* data, unsigned int len)
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
	Dict params;
	unsigned long int ident = 0;

	if (! decode_preamble(preamble, preamble_len, to, from, ident, params)) {
		return 0;
	}

	return new Packet(to.rbuf(), from.rbuf(), ident, params, Buffer(msg, msg_len));
}

Packet Packet::change_msg(const Buffer& msg) const
{
	return Packet(this->to(), this->from(), this->ident(), this->params(), msg);
}

Packet Packet::append_param(const char* key, const char* value) const
{
	Dict p = this->params();
	p.put(key, value);
	return Packet(this->to(), this->from(), this->ident(), p, this->msg());
}

bool encode_param(const Buffer& k, const Buffer *v, void* vs)
{
	char scratchpad[251];
	Buffer *b = (Buffer*) vs;
	if (v) {
		snprintf(scratchpad, sizeof(scratchpad) - 1, ",%s=%s", k.rbuf(), v->rbuf());
	} else {
		snprintf(scratchpad, sizeof(scratchpad) - 1, ",%s", k.rbuf());
	}
	b->append(scratchpad, strlen(scratchpad));
	printf("encode_param %s %s\n", scratchpad, b->rbuf());
	return true; // do not stop foreach
}

Buffer Packet::encode_params(unsigned long int ident, const Dict &params)
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
	char *w = b.wbuf();

	for (unsigned int i = 0; i < _to.length(); ++i) {
		*w++ = _to.rbuf()[i];
	}
	*w++ = '<';
	for (unsigned int i = 0; i < _from.length(); ++i) {
		*w++ = _from.rbuf()[i];
	}
	*w++ = ':';
	for (unsigned int i = 0; i < _sparams.length(); ++i) {
		*w++ = _sparams.rbuf()[i];
	}
	*w++ = ' ';
	memcpy(w, _msg.rbuf(), _msg.length());

	return b;
}

Buffer Packet::encode_l2() const
{
	Buffer b = encode_l3();

	memset(rs_decoded, 0, sizeof(rs_decoded));
	memcpy(rs_decoded, b.rbuf(), b.length());
	if (b.length() <= MSGSIZE_SHORT) {
		rs_short.Encode(rs_decoded, rs_encoded);
		b.append(rs_encoded + MSGSIZE_SHORT, REDUNDANCY);
	} else {
#ifdef __AVR__
		// truncate packet
		rs_short.Encode(rs_decoded, rs_encoded);
		b.append(rs_encoded + MSGSIZE_SHORT, REDUNDANCY);
#else
		rs_long.Encode(rs_decoded, rs_encoded);
		b.append(rs_encoded + MSGSIZE_LONG, REDUNDANCY);
#endif
	}

	return b;
}

const char* Packet::signature() const
{
	return _signature.rbuf();
}

bool Packet::is_dup(const Packet& other) const
{
	return strcmp(this->signature(), other.signature()) == 0;
}

Buffer Packet::repr() const
{
	char scratchpad[255];
	snprintf(scratchpad, 254, "pkt %s < %s : %s msg %s",
		_to.rbuf(), _from.rbuf(), _sparams.rbuf(), _msg.rbuf());
	return Buffer(scratchpad);
}
const char* Packet::to() const
{
	return _to.rbuf();
}

const char* Packet::from() const
{
	return _from.rbuf();
}

unsigned long int Packet::ident() const
{
	return _ident;
}

const Dict& Packet::params() const
{
	return _params;
}

const Buffer& Packet::msg() const
{
	return _msg;
}
