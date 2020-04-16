// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

// Automatic handlers for certain application protocols

#ifndef _HANDLER_H
#define _HANDLER_H

#include "Packet.h"
#include "Pointer.h"
#include "Callsign.h"

class Handler {
public:
	virtual Ptr<Packet> handle(const Packet &, const Callsign &) = 0;
	virtual ~Handler() {}
};

class Ping: public Handler {
public:
	virtual Ptr<Packet> handle(const Packet &, const Callsign &);
	virtual ~Ping() {}
};

class Rreq: public Handler {
public:
	virtual Ptr<Packet> handle(const Packet &, const Callsign &);
	virtual ~Rreq() {}
};

#endif
