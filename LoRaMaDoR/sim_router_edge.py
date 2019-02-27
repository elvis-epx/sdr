#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time
from sim_packet import Packet
from sim_router_a import AbstractRouter, ROUTER_VERBOSITY

# FIXME

# FIXME flexible TTL x detected network size

class Router(AbstractRouter):
	def __init__(self, callsign, helper):
		super().__init__(callsign, helper)
		# FIXME expire edges (possibly in superclass)
		async def send_qm():
			await asyncio.sleep(random.random() * 10)
			while True:
				self.send_qm()
				await asyncio.sleep(20 + random.random() * 10)
		loop = asyncio.get_event_loop()
		loop.create_task(send_qm())

	def learn(self, to, fr0m, rssi):
		if to == fr0m:
			raise Exception("#### FATAL %s <- %s" % (to, fr0m))

		cost = -rssi

		if to not in self.edges:
			self.edges[to] = {}
			self.sent_edges[to] = {}

		if fr0m not in self.edges[to]:
			if ROUTER_VERBOSITY > 90:
				print("%s rt: learnt %s < %s rssi %d" \
					% (self.callsign, to, fr0m, rssi))
			self.edges[to][fr0m] = cost
			self.sent_edges[to][fr0m] = False
		else:
			old_cost = self.edges[to][fr0m]
			if abs(cost - old_cost) > 10:
				print("%s rt: cost chg %s < %s rssi %d" \
					% (self.callsign, to, fr0m, rssi))
				self.edges[to][fr0m] = cost
				self.sent_edges[to][fr0m] = False

		if ROUTER_VERBOSITY >= 50:
			learnt_edges = sum(len(v.keys()) for k, v in self.edges.items())
			total_edges = self.helper['total_edges']()
			pp = 100 * learnt_edges / total_edges
			print("%s rt knows %.1f%% of the graph" % (self.callsign, pp))
			# print("\tknows: ", self.edges)

	def _parse_qm_item(self, msg):
		info = msg.strip().split(":")
		if len(info) != 3:
			return None, None, None
		to, fr0m, rssi = tuple(info)

		if not to or not fr0m or to == fr0m:
			return None, None, None
		if to[0] == "Q" or fr0m[0] == "Q":
			return None, None, None

		try:
			rssi = float(rssi)
		except ValueError:
			return None, None, None

		return to, fr0m, rssi

	def _parse_qm(self, msg):
		ei = 0
		edges = {}
		infos = msg.strip().upper().split(" ")
		if not infos:
			return None
		for info in infos:
			to, fr0m, rssi = self._parse_qm_item(info)
			if not to:
				return None
			ei += 1
			edges[ei] = {"to": to, "from": fr0m, "rssi": rssi}
		return edges

	def handle_pkt(self, radio_rssi, pkt):
		if pkt.to == "QB" and pkt.fr0m != "QB" and pkt.fr0m != self.callsign:
			# Beacon packet from neighbor
			print("%s rt: got QB pkt %s" % (self.callsign, pkt))
			kind = "QB"
			edges = {"qb": {"to": self.callsign, "from": pkt.fr0m, "rssi": radio_rssi}}
		elif pkt.to == "QM" and pkt.fr0m == "QM":
			# QM packet, sent by another router
			print("%s rt: got QM pkt %s" % (self.callsign, pkt))
			kind = "QM"
			edges = self._parse_qm(pkt.msg)
			if not edges:
				if ROUTER_VERBOSITY > 40:
					print("%s: Bad QM msg %s", (self.callsign, pkt.msg))
				return False
		else:
			return False

		for k, edge in edges.items():
			self.learn(edge["to"], edge["from"], edge["rssi"])

		return kind == "QM"

	def send_qm(self):
		# Collect and send QM packet with unpublished edges
		msg = ""
		for to, v in self.sent_edges.items():
			for fr0m, published in v.items():
				if not published:
					self.sent_edges[to][fr0m] = True
					cost = self.edges[to][fr0m]
					rssi = -cost
					if msg:
						msg += " "
					msg += "%s:%s:%.0f" % (to, fr0m, rssi)
					if len(msg) > 50:
						break
			if len(msg) > 50:
				break

		if not msg:
			return

		pkt = Packet("QM", "", "QM", self.helper['max_ttl'](), msg)

		if ROUTER_VERBOSITY > 50:
			print("%s: rt publishing %s" % \
				(self.callsign, msg))

		self.helper['sendmsg'](pkt)
