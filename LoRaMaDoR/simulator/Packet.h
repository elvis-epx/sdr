/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include "Utility.h"

struct Packet {
	Packet(const char *to, const char *from, unsigned long int ident, 
		const Dict& params, const Buffer& msg);
	~Packet();

	static Packet* decode_l2(const char* data, unsigned int len);

	/* public for unit testing */
	static Packet* decode_l3(const char* data, unsigned int len);
	static Packet* decode_l3(const char *data);

	Packet(const Packet &) = delete;
	Packet(Packet &&);
	Packet() = delete;
	Packet& operator=(const Packet &) = delete;
	bool operator==(const Packet &) = delete;

	Packet change_msg(const Buffer& msg) const;
	Packet append_param(const char *key, const char *value) const;
	Buffer encode_l2() const;

	/* public for unit testing */
	Buffer encode_l3() const;

	bool is_dup(const Packet& other) const;
	Buffer repr() const;
	const char *signature() const;
	const char *to() const;
	const char *from() const;
	unsigned long int ident() const;
	const Dict& params() const;
	const Buffer& msg() const;

	/* public for unit testing */
	static bool check_callsign(const Buffer&);
	static bool parse_params(const char *data, unsigned int len,
		unsigned long int &ident, Dict &params);
	static bool parse_params(const char *data,
		unsigned long int &ident, Dict &params);
	static Buffer encode_params(unsigned long int ident, const Dict&);

private:
	Buffer _to;
	Buffer _from;
	const unsigned long int _ident;
	const Dict _params;
	Buffer _sparams;
	Buffer _signature;
	const Buffer _msg;
};
