/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include "WString.h"
#include "Utility.h"

struct Packet {
	Packet(const String &to, const String &from, unsigned long int ident, 
		const Dict& params, const Buffer& msg);

	static Packet* decode(const char* data, unsigned int len);
	static Packet* decode(const String &data);

	Packet(const Packet &) = default;
	Packet() = delete;
	Packet& operator=(const Packet &) = delete;
	bool operator==(const Packet &) = delete;

	Packet change_msg(const Buffer& msg) const;
	Packet append_param(const String& key, const String* value) const;
	Buffer encode() const;
	String encode_params() const;
	bool is_dup(const Packet& other) const;
	String repr() const;
	String signature() const;

	static bool check_callsign(const String& s);
	static bool parse_params(const char *data, unsigned int len,
		unsigned long int &ident, Dict &params);
	static bool parse_params(const String &data,
		unsigned long int &ident, Dict &params);

	String to;
	String from;
	const unsigned long int ident;
	const Dict params;
	const Buffer msg;
};
