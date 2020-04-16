// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#include <string.h>
#include "Modifier.h"

Ptr<Packet> Rreqi::modify(const Packet &pkt, const Callsign &me)
{
	if (! pkt.to().isQ()) {
		// not QB, QC, etc.
		if (pkt.params().has("RREQ") || pkt.params().has("RRSP")) {
			Buffer new_msg = pkt.msg();
			new_msg.append('|');
			new_msg.append_str(me.buf());
			return pkt.change_msg(new_msg);
		}
	}
	return Ptr<Packet>(0);
}

Ptr<Packet> RetransMark::modify(const Packet &pkt, const Callsign &me)
{
	if (! pkt.params().has("R")) {
		Params new_params = pkt.params();
		new_params.put_naked("R");
		return pkt.change_params(new_params);
	}
	return Ptr<Packet>(0);
}
