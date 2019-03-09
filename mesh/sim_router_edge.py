#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time
from sim_packet import Packet

MAPPER_VERBOSITY = 100

SECONDS = 1.0
MINUTES = 60 * SECONDS

FIRST_BEACON_TIME = 1 * SECONDS
SEND_QM_TIME = 2 * SECONDS
BEACON_TIME = 1 * MINUTES
EDGE_SHARE_AGAIN_TIME = 2 * BEACON_TIME
EDGE_EXPIRATION_TIME = 2 * EDGE_SHARE_AGAIN_TIME

# FIXME

# FIXME flexible TTL x detected network size

class Edge:
	def __init__(self, rssi, next_share, expiry):
		self.rssi = rssi
		self.next_share = next_share
		self.expiry = expiry

class Mapper:
	def __init__(self, callsign, helper):
		self.callsign = callsign
		self.helper = helper
		self.graph = {}
		self.beacon_counter = 0

		loop = asyncio.get_event_loop()

		loop.create_task(self.sch_send_qm())
		loop.create_task(self.sch_send_beacon())
		loop.create_task(self.expire())

	async def sch_send_qm(self):
		while True:
			await asyncio.sleep(SEND_QM_TIME * (0.5 + random.random()))
			self.send_qm()

	async def sch_send_beacon(self):
		await asyncio.sleep(FIRST_BEACON_TIME * (0.5 + random.random()))
		while True:
			self.send_beacon()
			await asyncio.sleep(BEACON_TIME * (0.5 + random.random()))

	# Expire graph edges
	async def expire(self):
		while True:
			await asyncio.sleep(60)
			self.do_expire()

	def do_expire(self):
		now = time.time()
		expired = []
		for to, allfrom in self.graph.items():
			for fr0m, e in allfrom.items():
				if e.expiry < now:
					if MAPPER_VERBOSITY > 80:
						print("%s map: expiring edge %s < %s" % \
							(self.callsign, to, fr0m))
					expired.append((to, fr0m))

		for to, fr0m in expired:
			del self.graph[to][fr0m]

	# Calculate next 'via' station.
	def learn(self, to, fr0m, rssi):
		if to == fr0m:
			raise Exception("#### FATAL %s <- %s" % (to, fr0m))

		now = time.time()

		if to not in self.graph:
			self.graph[to] = {}

		if fr0m not in self.graph[to]:
			if MAPPER_VERBOSITY > 90:
				print("%s map: learnt %s < %s rssi %d" \
					% (self.callsign, to, fr0m, rssi))
			expiry = now + EDGE_EXPIRATION_TIME
			e = self.graph[to][fr0m] = Edge(rssi, 0, expiry)
		else:
			e = self.graph[to][fr0m]
			if abs(rssi - e.rssi) > 10:
				if MAPPER_VERBOSITY > 90:
					print("%s map: changed %s < %s rssi %d" \
						% (self.callsign, to, fr0m, rssi))
				e.next_share = 0
			else:
				if MAPPER_VERBOSITY > 90:
					print("%s map: refresh %s < %s rssi %d" \
						% (self.callsign, to, fr0m, rssi))
			e.rssi = rssi
			e.expiry = now + EDGE_EXPIRATION_TIME

		self.helper['send_to_router'](to, fr0m, e.rssi, e.expiry)

		if MAPPER_VERBOSITY >= 50:
			learnt_edges = sum(len(v.keys()) for k, v in self.graph.items())
			total_edges = self.helper['total_edges']()
			pp = 100 * learnt_edges / total_edges
			print("%s rt knows %.1f%% of the graph" % (self.callsign, pp))

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
			print("%s map: got QB pkt %s" % (self.callsign, pkt))
			kind = "QB"
			edges = {"qb": {"to": self.callsign, "from": pkt.fr0m, "rssi": radio_rssi}}

		elif pkt.to == "QM" and pkt.fr0m == "QM":
			# QM packet, sent by another router
			print("%s map: got QM pkt %s" % (self.callsign, pkt))
			kind = "QM"
			edges = self._parse_qm(pkt.msg)
			if not edges:
				if MAPPER_VERBOSITY > 40:
					print("%s: Bad QM msg %s", (self.callsign, pkt.msg))
				return False

		else:
			return False

		for k, edge in edges.items():
			self.learn(edge["to"], edge["from"], edge["rssi"])

		return kind == "QM"

	# Send QB packet automatically, which is important for the algorithm
	def send_beacon(self):
		self.beacon_counter += 1
		msg = '%d' % self.beacon_counter
		pkt = Packet("QB", "", self.callsign, 1, msg)
		self.helper['sendmsg'](pkt)

	# Send QM packets to share learn graph edges
	def send_qm(self):
		now = time.time()
		msg = ""
		for to, v in self.graph.items():
			for fr0m, e in v.items():
				if e.next_share < now:
					e.next_share = now + EDGE_SHARE_AGAIN_TIME
					if msg:
						msg += " "
					msg += "%s:%s:%.0f" % (to, fr0m, e.rssi)
					if len(msg) > 50:
						break
			if len(msg) > 50:
				break

		if not msg:
			return

		pkt = Packet("QM", "", "QM", self.helper['max_ttl'](), msg)

		if MAPPER_VERBOSITY > 50:
			print("%s: rt publishing %s" % \
				(self.callsign, msg))

		self.helper['sendmsg'](pkt)

