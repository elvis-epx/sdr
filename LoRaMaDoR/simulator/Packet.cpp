/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include "Packet.h"

static String encode_params(unsigned long int ident, const Dict& params)
{
}

static bool check_callsign(const String& s)
{
}

static bool parse_symbol_param(const String& s, String &key, String& value)
{
}

static bool parse_ident_param(const String& s, unsigned long int &ident)
{
}

static bool parse_param(const String& s, unsigned long int &ident,
	String& key, String& value)
{
}

static bool parse_params(const String& s, unsigned long int &ident, Dict &params)
{
}

static bool decode_preamble(const String& s, String& to, String& from,
	unsigned long int& ident, Dict& params)
{
}

Packet(const String &to, const String &from, unsigned long int ident, 
		const Dict& params, const Buffer& msg): 
			to(to), from(from), ident(ident), params(parms), msg(msg)
{
	
}

static Packet* Packet::decode(const String& data)
{
}

Packet Packet::change_msg(const String& msg) const
{
	return Packet(this->to, this->from, this->ident, this->params, msg);
}

Packet Packet::append_param(const String& key, const String& value) const
{
	Params p = this->params.copy();
	p.put(key, value);
	return Packet(this->to, this->from, this->ident, p, this->msg);
}

const Buffer Packet::encode() const
{
	return encoded;
}

int Packet::length() const
{
	return encoded.length();
}

bool Packet::is_dup(const Packet& other) const
{
	return this->signature == other.signature
}

String Packet::repr() const
{
}
