// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#include <string.h>
#include "Handler.h"

Packet* Ping::handle(const Packet &pkt, const char* callsign)
{
	Packet *ret = 0;
	if (strlen(pkt.to()) > 2 && pkt.params().has("PING")) {
		Params pong = Params();
		pong.put("PONG", None);
		ret = new Packet(pkt.from(), callsign, pkt.ident(), pong, pkt.msg());
	}
	return ret;
}

Packet* Rreq::handle(const Packet &pkt, const char* callsign)
{
	Packet *ret = 0;
	if (strlen(pkt.to()) > 2 && pkt.params().has("RREQ")) {
		Buffer msg = pkt.msg();
		msg.append("\r\n", 2);
		Params rrsp = Params();
		rrsp.put("RRSP", None);
		ret = new Packet(pkt.from(), callsign, pkt.ident(), rrsp, msg);
	}
	return ret;
}
