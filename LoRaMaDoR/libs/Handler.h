// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

// Automatic handlers for certain application protocols

#ifndef _HANDLER_H
#define _HANDLER_H

#include "Packet.h"
#include "Pointer.h"

class Handler {
public:
	virtual Ptr<Packet> handle(const Packet &, const char *) = 0;
	virtual ~Handler() {}
};

class Ping: public Handler {
public:
	virtual Ptr<Packet> handle(const Packet &, const char *);
	virtual ~Ping() {}
};

class Rreq: public Handler {
public:
	virtual Ptr<Packet> handle(const Packet &, const char *);
	virtual ~Rreq() {}
};

#endif
