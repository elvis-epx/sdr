/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include "WString.h"
#include "Utility.h"

struct Packet {
	Packet(const String &to, const String &from, unsigned long int ident, 
		const Dict& params, const Buffer& msg);

	Packet(const Packet &) = delete;
	Packet() = delete;
	Packet& operator=(const Packet &) = delete;
	bool operator==(const Packet &) = delete;

	String to() const;
	String from() const;
	unsigned long int ident() const;
	Dict params() const;
	Buffer msg() const;

	Packet change_msg(const String& msg) const;
	Packet append_param(const String& key, const String& value) const;
	String encode() const;
	int length() const;
	String signature() const;
	bool is_dup(const Packet& other) const;
	String repr() const;

	static Packet* decode(const String& data);

	String _to;
	String _from;
	unsigned long int _ident;
	Dict _params;
	Buffer _msg;
	
	static String encode_params(unsigned long int ident, const Dict& params);
	static bool check_callsign(const String& s);
	static bool parse_symbol_param(const String& s, String &key, String& value);
	static bool parse_ident_param(const String& s, unsigned long int &ident);
	static bool parse_param(const String& s, unsigned long int &ident,
		String& key, String& value);
	static bool parse_params(const String& s, unsigned long int &ident, Dict &params);
	static bool decode_preamble(const String& s, String& to, String& from,
		unsigned long int& ident, Dict& params);
};
