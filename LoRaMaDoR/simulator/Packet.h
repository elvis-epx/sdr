/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include "Utility.h"

struct Packet {
	Packet(const char *to, const char *from, unsigned long int ident, 
		const Dict& params, const Buffer& msg);

	static Packet* decode(const char* data, unsigned int len);
	static Packet* decode(const char *data);

	Packet(const Packet &) = default;
	Packet() = delete;
	Packet& operator=(const Packet &) = delete;
	bool operator==(const Packet &) = delete;

	Packet change_msg(const Buffer& msg) const;
	Packet append_param(const char *key, const char *value) const;
	Buffer encode() const;
	bool is_dup(const Packet& other) const;
	char *repr() const;
	const char *signature() const;
	const char *to() const;
	const char *from() const;
	unsigned long int ident() const;
	const Dict& params() const;
	const Buffer& msg() const;

	static bool check_callsign(const char *s);
	static bool parse_params(const char *data, unsigned int len,
		unsigned long int &ident, Dict &params);
	static bool parse_params(const char *data,
		unsigned long int &ident, Dict &params);
	static char *encode_params(unsigned long int ident, const Dict&);

private:
	char *_to;
	char *_from;
	const unsigned long int _ident;
	const Dict _params;
	char *_sparams;
	char *_signature;
	const Buffer _msg;
};
