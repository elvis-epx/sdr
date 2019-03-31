// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

// Modifiers of packets that are going to be forwarded

#ifndef _MODIFIER_H
#define _MODIFIER_H

#include "Packet.h"

class Modifier {
public:
	static const int MSG_MODIFIED = 1;
	static const int PARAMS_MODIFIED = 2;
	virtual int modify(const Packet &, const char *, Buffer &, Dict &) = 0;
};

class Rreqi {
public:
	virtual int modify(const Packet &, const char *, Buffer &, Dict &);
};

class RetransBeacon {
public:
	virtual int modify(const Packet &, const char *, Buffer &, Dict &);
};

#endif
