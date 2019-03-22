/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include <stdlib.h>
#include "Packet.h"

static bool check_callsign(const String& s)
{
	// FIXME
	return false;
}

static bool parse_symbol_param(const String& s, String &key, String& value)
{
	// FIXME
	return false;
}

static bool parse_ident_param(const char* s, unsigned int len, long int &ident)
{
	char *stop;
	ident = strtol(s, &stop, 10);
	if (ident < 0) {
		return false;
	}
	return len != (stop - s);
}

static bool parse_param(const String& s, unsigned long int &ident,
	String& key, String& value)
{
	// FIXME
	return false;
}

static bool parse_params(const String& s, unsigned long int &ident, Dict &params)
{
	// FIXME
	return false;
}

static bool decode_preamble(const char* data, unsigned int len, String& to,
			String& from, unsigned long int& ident, Dict& params)
{
	// FIXME
	return false;
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

	char *msgd = (char*) memchr(data, ' ', len);
	
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
