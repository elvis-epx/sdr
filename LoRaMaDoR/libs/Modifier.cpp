// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#include <string.h>
#include "Modifier.h"

Ptr<Packet> Rreqi::modify(const Packet &pkt, const char* callsign)
{
	if (strlen(pkt.to()) > 2) {
		// not QB, QC, etc.
		if (pkt.params().has("RREQ") || pkt.params().has("RRSP")) {
			Buffer new_msg = pkt.msg();
			new_msg.append("|", 1);
			new_msg.append(callsign, strlen(callsign));
			return pkt.change_msg(new_msg);
		}
	}
	return 0;
}

Ptr<Packet> RetransBeacon::modify(const Packet &pkt, const char* callsign)
{
	if ((strcmp(pkt.to(), "QB") == 0) || (strcmp(pkt.to(), "QC") == 0)) {
		if (! pkt.params().has("R")) {
			Params new_params = pkt.params();
			new_params.put("R", None);
			return pkt.change_params(new_params);
		}
	}
	return 0;
}
