// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#include <string.h>
#include "Handler.h"
#include "Network.h"

Ptr<Packet> Ping::handle(const Packet &pkt, Network& net)
{
	if ((!pkt.to().isQ() || pkt.to().is_localhost()) && pkt.params().has("PING")) {
		Params pong = Params();
		pong.set_ident(net.get_next_pkt_id());
		pong.put_naked("PONG");
		return Ptr<Packet>(new Packet(pkt.from(), net.me(), pong, pkt.msg()));
	}
	return Ptr<Packet>(0);
}

Ptr<Packet> Rreq::handle(const Packet &pkt, Network& net)
{
	if ((!pkt.to().isQ() || pkt.to().is_localhost()) && pkt.params().has("RREQ")) {
		Buffer msg = pkt.msg();
		msg.append('|');
		Params rrsp = Params();
		rrsp.set_ident(net.get_next_pkt_id());
		rrsp.put_naked("RRSP");
		return Ptr<Packet>(new Packet(pkt.from(), net.me(), rrsp, msg));
	}
	return Ptr<Packet>(0);
}
