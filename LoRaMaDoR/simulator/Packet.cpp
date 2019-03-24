/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "Packet.h"

bool Packet::check_callsign(const char* s)
{
	unsigned int length = strlen(s);

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

static bool parse_symbol_param(const char *data, unsigned int len, char*& key, char*& value)
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

	key = strndup(data, skey_len);

	if (equal) {
		value = strndup(equal + 1, svalue_len);
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
		unsigned long int &ident, char *&key, char *&value)
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
		char *key;
		char *value = 0;

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
			free(key);
			free(value);
		}

		data += advance_len;
		len -= advance_len;
	}

	// valid only if there was an ident among params
	return ident;
}

static bool decode_preamble(const char* data, unsigned int len,
		char *&to, char *&from, unsigned long int& ident, Dict& params)
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

	to = strndup(data, d1 - data);
	printf("parsed to: %s\n", to);
	from = strndup(d1 + 1, d2 - d1 - 1);
	printf("parsed from: %s\n", from);

	uppercase(to);
	uppercase(from);

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
			_ident(ident), _params(params), _msg(msg)
{
	_to = strdup(to);
	_from = strdup(from);
	_sparams = encode_params(_ident, _params);
	uppercase(_to);
	uppercase(_from);

	char scratchpad[32];
	snprintf(scratchpad, 31, "%s:%ld", _from, _ident);
	_signature = strdup(scratchpad);
}

Packet::Packet(Packet &&model): _ident(model._ident), _params(model._params), _msg(model._msg)
{
	_to = model._to;
	_from = model._from;
	_sparams = model._sparams;
	_signature = model._signature;

	model._to = 0;
	model._from = 0;
	model._sparams = 0;
	model._signature = 0;
}

Packet::~Packet()
{
	free(_to);
	free(_from);
	free(_sparams);
	free(_signature);
}

Packet* Packet::decode(const char* data)
{
	return decode(data, strlen(data));
}

Packet* Packet::decode(const char* data, unsigned int len)
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

	char *to = 0;
	char *from = 0;
	Dict params;
	unsigned long int ident = 0;

	if (! decode_preamble(preamble, preamble_len, to, from, ident, params)) {
		free(to);
		free(from);
		return 0;
	}

	Packet *p = new Packet(to, from, ident, params, Buffer(msg, msg_len));
	free(to);
	free(from);
	return p;
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

bool encode_param(const char* k, const char *v, void* vs)
{
	char scratchpad[251];
	char **s = (char**) vs;
	if (v) {
		snprintf(scratchpad, sizeof(scratchpad) - 1, "%s,%s=%s", *s, k, v);
	} else {
		snprintf(scratchpad, sizeof(scratchpad) - 1, "%s,%s", *s, k);
	}
	free(*s);
	*s = strdup(scratchpad);
	return true; // do not stop foreach
}

char* Packet::encode_params(unsigned long int ident, const Dict &params)
{
	char sident[20];
	sprintf(sident, "%ld", ident);
	char *p = strdup(sident);
	params.foreach(&p, &encode_param);
	return p;
}

Buffer Packet::encode() const
{
	unsigned int to_length = strlen(_to);
	unsigned int from_length = strlen(_from);
	unsigned int params_length = strlen(_sparams);

	unsigned int len = to_length + 1 + from_length + 1 + params_length + 1 + _msg.length();
	Buffer b(len);
	char *w = b.wbuf();

	for (unsigned int i = 0; i < to_length; ++i) {
		*w++ = _to[i];
	}
	*w++ = '<';
	for (unsigned int i = 0; i < from_length; ++i) {
		*w++ = _from[i];
	}
	*w++ = ':';
	for (unsigned int i = 0; i < params_length; ++i) {
		*w++ = _sparams[i];
	}
	*w++ = ' ';
	memcpy(w, _msg.rbuf(), _msg.length());

	return b;
}

const char* Packet::signature() const
{
	return _signature;
}

bool Packet::is_dup(const Packet& other) const
{
	return strcmp(this->signature(), other.signature()) == 0;
}

char* Packet::repr() const
{
	char scratchpad[255];
	snprintf(scratchpad, 254, "pkt %s < %s : %s msg %s",
		_to, _from, _sparams, _msg.rbuf());
	return strdup(scratchpad);
}
const char* Packet::to() const
{
	return _to;
}

const char* Packet::from() const
{
	return _from;
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
