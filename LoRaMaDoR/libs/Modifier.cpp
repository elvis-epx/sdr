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
			new_msg.append("|");
			new_msg.append(me.buf());
			return pkt.change_msg(new_msg);
		}
	}
	return 0;
}

Ptr<Packet> RetransMark::modify(const Packet &pkt, const Callsign &me)
{
	if (! pkt.params().has("R")) {
		Params new_params = pkt.params();
		new_params.put("R", None);
		return pkt.change_params(new_params);
	}
	return 0;
}
