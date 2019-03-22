/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

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

static bool parse_ident_param(const String& s, unsigned long int &ident)
{
	// FIXME
	return false;
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

static bool decode_preamble(const String& s, String& to, String& from,
	unsigned long int& ident, Dict& params)
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

Packet* Packet::decode(const String& data)
{
	// FIXME
	return 0;
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
	return Buffer("FIXME", 5);
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
