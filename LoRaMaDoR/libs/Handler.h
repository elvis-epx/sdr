// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

// Automatic handlers for certain application protocols

#ifndef __HANDLER_H
#define __HANDLER_H

#include "Packet.h"
#include "Pointer.h"
#include "Callsign.h"

class Network;

class Handler {
public:
	virtual Ptr<Packet> handle(const Packet&, Network&) = 0;
	virtual ~Handler() {}
};

class Ping: public Handler {
public:
	virtual Ptr<Packet> handle(const Packet&, Network&);
	virtual ~Ping() {}
};

class Rreq: public Handler {
public:
	virtual Ptr<Packet> handle(const Packet&, Network&);
	virtual ~Rreq() {}
};

#endif
