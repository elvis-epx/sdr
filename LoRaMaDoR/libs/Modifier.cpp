// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#include <string.h>
#include "Modifier.h"

int Rreqi::modify(const Packet &pkt, const char* callsign, Buffer &msg, Dict& params)
{
	if (strlen(pkt.to()) > 2) {
		// not QB, QC, etc.
		if (params.has("RREQ") || params.has("RRSP")) {
			msg.append("\r\n", 2);
			msg.append(callsign, strlen(callsign));
			return Modifier::MSG_MODIFIED;
		}
	}
	return 0;
}

int RetransBeacon::modify(const Packet &pkt, const char* callsign, Buffer &msg, Dict& params)
{
	if ((strcmp(pkt.to(), "QB") == 0) || (strcmp(pkt.to(), "QC") == 0)) {
		if (! params.has("R")) {
			params.put("R");
			return Modifier::PARAMS_MODIFIED;
		}
	}
	return 0;
}
