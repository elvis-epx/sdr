// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

// Modifiers of packets that are going to be forwarded

#ifndef _MODIFIER_H
#define _MODIFIER_H

#include "Packet.h"

class Modifier {
public:
	virtual Packet* modify(const Packet &, const char *) = 0;
};

class Rreqi: public Modifier {
public:
	virtual Packet* modify(const Packet &, const char *);
};

class RetransBeacon: public Modifier {
public:
	virtual Packet* modify(const Packet &, const char *);
};

#endif
