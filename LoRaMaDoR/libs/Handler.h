// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

// Automatic handlers for certain application protocols

#ifndef _HANDLER_H
#define _HANDLER_H

#include "Packet.h"

class Handler {
public:
	virtual Packet* handle(const Packet &, const char *) = 0;
};

class Ping: public Handler {
public:
	virtual Packet* handle(const Packet &, const char *);
};

class Rreq: public Handler {
public:
	virtual Packet* handle(const Packet &, const char *);
};

#endif
