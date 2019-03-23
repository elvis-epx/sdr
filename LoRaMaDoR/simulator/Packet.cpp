/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include <stdlib.h>
#include "Packet.h"

static bool check_callsign(String& s)
{
	s.toUpperCase();

	if (s.length() < 2) {
		return false;
	} else if (s.length() == 2) {
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

		unsigned int ssid_delim = s.indexOf('-');
		String prefix;

		if (ssid_delim >= 0) {
			prefix = s.substring(0, ssid_delim);
			String ssid = s.substring(ssid_delim + 1);
			if (ssid.length() <= 0 || ssid.length() > 2) {
				return false;
			}
			bool sig = false;
			for (int i = 1; i < ssid.length(); ++i) {
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
			prefix = s;
		}

		if (prefix.length() > 7 || prefix.length() < 4) {
			return false;
		}
		for (int i = 1; i < prefix.length(); ++i) {
			char c = prefix[i];
			if (c >= '0' && c <= '9') {
			} else if (c >= 'A' && c <= 'Z') {
			} else {
				return false;
			}
		}
	}

	return true;
}

static bool parse_symbol_param(const char *data, unsigned int len, String &key, String*& value)
{
	if (! len) {
		return false;
	}

	unsigned int skey_len = 0;
	unsigned int svalue_len = 0;

	// find '=' separator, if exists
	const char *equal = (const char*) memchr(data, ',', len);

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
	for (int i = 0; i < skey_len; ++i) {
		char c = data[i];
		if (c >= 'a' && c <= 'z') {
		} else if (c >= 'A' && c <= 'Z') {
		} else if (c >= '0' && c <= '9') {
		} else {
			return false;
		}
	}
	
	// check value characters, if there is a value
	if (equal) {
		for (int i = 0; i < svalue_len; ++i) {
			char c = equal[1 + i];
			if (strchr("= ,:<", c)) {
				return false;
			}
		}
	}

	// convert key name to String
	char *skey = strndup(data, skey_len);
	key = String(skey);
	free(skey);

	// convert value to String, or make it null (note: empty != null)
	if (equal) {
		char *svalue = strndup(equal + 1, svalue_len);
		value = new String(svalue); // must be freed by caller
		free(svalue);
	} else {
		value = 0;
	}

	return true;
}

static bool parse_ident_param(const char* s, unsigned int len, unsigned long int &ident)
{
	char *stop;
	ident = strtol(s, &stop, 10);
	if (ident < 0) {
		return false;
	}
	return len != (stop - s);
}

static bool parse_param(const char* data, unsigned int len,
		unsigned long int &ident, String& key, String*& value)
{
	if (! len) {
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

	return false;
}

static bool parse_params(const char *param, unsigned int len,
		unsigned long int &ident, Dict &params)
{
	ident = 0;

	while (len > 0) {
		unsigned int param_len;
		unsigned int advance_len;

		const char *comma = (const char*) memchr(param, ',', len);
		if (! comma) {
			// last, or only, param
			param_len = len;
			advance_len = len;
		} else {
			param_len = comma - param;
			advance_len = param_len + 1;
		}

		if (! param_len) {
			return false;
		}

		unsigned long int tident = 0;
		String key;
		String* value = 0;

		if (! parse_param(param, param_len, tident, key, value)) {
			free(value);
			return false;
		}
		if (tident) {
			// parameter is ident
			ident = tident;
		} else {
			// parameter is key=value or naked key
			key.toUpperCase();
			params.put(key, value);
			free(value);
		}

		param += advance_len;
		len -= advance_len;
	}

	// valid only if there was an ident among params
	return ident;
}

static bool decode_preamble(const char* data, unsigned int len,
		String& to, String& from, unsigned long int& ident, Dict& params)
{
	const char *d1 = (const char*) memchr(data, '<', len);
	const char *d2 = (const char*) memchr(data, ':', len);

	if (d1 == 0 || d2 == 0) {
		// delimiters not found
		return false;
	} else if (d1 >= d2)  {
		// delimiters swapped or null second section
		return false;
	} else if ((d2 - data) >= len) {
		// empty third section
		return false;
	} else if (d1 == data) {
		// empty first section
		return false;
	}

	char *to_s = strndup(data, d1 - data);
	char *from_s = strndup(d1 + 1, d2 - d1 - 1);
	to = to_s;
	from = from_s;
	free(to_s);
	free(from_s);

	if (!check_callsign(to) || !check_callsign(from)) {
		return false;
	}

	const char *sparams = d2 + 1;
	unsigned int sparams_len = len - (d2 - data) - 1;
	if (! parse_params(sparams, sparams_len, ident, params)) {
		return false;
	}

	return true;
}

Packet::Packet(const String &to, const String &from, unsigned long int ident, 
			const Dict& params, const Buffer& msg): 
		to(to), from(from), ident(ident), params(params), msg(msg)
{
	// intentionally empty
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

	String to, from;
	Dict params;
	unsigned long int ident = 0;

	if (! decode_preamble(preamble, preamble_len, to, from, ident, params)) {
		return 0;
	}

	return new Packet(to, from, ident, params, Buffer(msg, msg_len));
}

Packet Packet::change_msg(const Buffer& msg) const
{
	return Packet(this->to, this->from, this->ident, this->params, msg);
}

Packet Packet::append_param(const String& key, const String* value) const
{
	Dict p = this->params;
	p.put(key, value);
	return Packet(this->to, this->from, this->ident, p, this->msg);
}

bool encode_param(const String &k, const String *v, void* vs)
{
	String *s = (String*) vs;
	String kc = k;
	kc.toUpperCase();
	if (v) {
		*s += "," + kc + "=" + *v;
	} else {
		*s += "," + kc;
	}
	return true; // do not stop foreach
}

String Packet::encode_params() const
{
	String p = String(this->ident);
	this->params.foreach(&p, &encode_param);
	return p;
}

Buffer Packet::encode() const
{
	String params = this->encode_params();
	unsigned int len = to.length() + 1 + from.length() + 1 + params.length() + 1 + msg.length();
	Buffer b(len);
	char *w = b.wbuf();

	for (int i = 0; i < to.length(); ++i) {
		*w++ = to[i];
	}
	*w++ = '<';
	for (int i = 0; i < from.length(); ++i) {
		*w++ = from[i];
	}
	*w++ = ':';
	for (int i = 0; i < params.length(); ++i) {
		*w++ = params[i];
	}
	*w++ = ' ';
	for (int i = 0; i < msg.length(); ++i) {
		*w++ = msg.rbuf()[i];
	}

	return b;
}

String Packet::signature() const
{
	return this->from + ":" + String(this->ident);
}

bool Packet::is_dup(const Packet& other) const
{
	return this->signature() == other.signature();
}

String Packet::repr() const
{
	return String("pkt ") + this->to + " < " + this->from + " : " +
		this->encode_params() + " msg " + this->msg.Str();
}
