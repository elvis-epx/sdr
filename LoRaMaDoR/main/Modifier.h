// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

// Modifiers of packets that are going to be forwarded

#ifndef _MODIFIER_H
#define _MODIFIER_H

#include "Packet.h"

class Modifier {
public:
	virtual Ptr<Packet> modify(const Packet &, const Callsign &) = 0;
	virtual ~Modifier() {}
};

class Rreqi: public Modifier {
public:
	virtual Ptr<Packet> modify(const Packet &, const Callsign &);
};

class RetransMark: public Modifier {
public:
	virtual Ptr<Packet> modify(const Packet &, const Callsign &);
};

#endif
