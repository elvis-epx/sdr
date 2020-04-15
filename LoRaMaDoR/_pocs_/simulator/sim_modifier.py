#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

# Modifiers of packets that are going to be forwarded

class Rreqi:
	@staticmethod
	def match(pkt):
		return ("RREQ" in pkt.params or "RRSP" in pkt.params) and len(pkt.to) > 2

	@staticmethod
	def handle(station, pkt):
		msg = pkt.msg + "\n" + station.callsign
		return None, msg

class RetransBeacon:
	@staticmethod
	def match(pkt):
		return len(pkt.to) == 2 and pkt.to in ("QB", "QC") and "R" not in pkt.params

	@staticmethod
	def handle(station, pkt):
		return {"R": None}, None

fwd_modifiers = [ Rreqi, RetransBeacon ]
