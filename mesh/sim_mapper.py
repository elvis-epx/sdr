#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time
from sim_packet import Packet

MAPPER_VERBOSITY = 100

FIRST_QN_TIME = 10
QN_TIME = 60

SEND_QM_TIME = 30
EDGE_EXPIRATION_TIME = 120

# FIXME

# FIXME flexible TTL x detected network size

class Edge:
	def __init__(self, rssi, expiry):
		self.rssi = rssi
		self.shared = False
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
		loop.create_task(self.sch_debug())

	async def sch_send_qm(self):
		while True:
			await asyncio.sleep(SEND_QM_TIME * (0.5 + random.random()))
			self.send_qm()

	async def sch_send_beacon(self):
		await asyncio.sleep(FIRST_QN_TIME * (0.5 + random.random()))
		while True:
			self.send_beacon()
			await asyncio.sleep(QN_TIME * (0.5 + random.random()))

	async def sch_debug(self):
		while True:
			await asyncio.sleep(30)
			learnt_edges = sum(len(v.keys()) for k, v in self.graph.items())
			total_edges = self.helper['total_edges']()
			pp = 100 * learnt_edges / total_edges
			print("%s rt knows %.1f%% of the graph" % (self.callsign, pp))

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

	# Learn graph edge
	def learn(self, qn, to, fr0m, rssi):
		if to == fr0m:
			print("#### FATAL learning %s <- %s" % (to, fr0m))
			return

		if not qn and to == self.callsign:
			# If I am X, X<Y edges are learnt from QN packets only
			return

		now = time.time()
		expiry = now + EDGE_EXPIRATION_TIME

		if to not in self.graph:
			self.graph[to] = {}

		if fr0m not in self.graph[to]:
			if MAPPER_VERBOSITY > 90:
				print("%s map: new edge %s < %s rssi %d" \
					% (self.callsign, to, fr0m, rssi))
		else:
			e = self.graph[to][fr0m]
			if e.rssi == rssi:
				if MAPPER_VERBOSITY > 90:
					print("%s map: already known %s < %s rssi %d" \
						% (self.callsign, to, fr0m, rssi))
				return
			if MAPPER_VERBOSITY > 90:
				print("%s map: refresh %s < %s rssi %d" \
					% (self.callsign, to, fr0m, rssi))

		self.graph[to][fr0m] = Edge(rssi, expiry)
		self.helper['send_to_router'](to, fr0m, rssi, expiry)

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
			rssi = int(rssi)
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
		if pkt.to == "QN":
			self.handle_pkt_qn(int(radio_rssi * 100), pkt)
			return False
		elif pkt.to == "QM":
			self.handle_pkt_qm(int(radio_rssi * 100), pkt)
			return True
		return False

	# Use beacon packet from neighbor
	def handle_pkt_qn(self, rssi, pkt):
		if pkt.fr0m == "QN" or pkt.fr0m == self.callsign:
			return

		# RSSI doubles as route version, so make it random
		rssi += 50 - int(random.random() * 100)

		print("%s map: got QN pkt %s" % (self.callsign, pkt))
		self.learn(True, self.callsign, pkt.fr0m, rssi)

	# QM packet
	def handle_pkt_qm(self, rssi, pkt):
		if pkt.fr0m != "QM":
			return

		print("%s map: got QM pkt %s" % (self.callsign, pkt))
		edges = self._parse_qm(pkt.msg)
		if not edges:
			if MAPPER_VERBOSITY > 40:
				print("%s: Bad QM msg %s", (self.callsign, pkt.msg))
			return
		for k, edge in edges.items():
			self.learn(False, edge["to"], edge["from"], edge["rssi"])

	# Send QN packet every n seconds
	def send_beacon(self):
		self.beacon_counter += 1
		msg = '%d' % self.beacon_counter
		pkt = Packet("QN", "", self.callsign, 1, msg)
		self.helper['sendmsg'](pkt)

	# Generate QM msg with fresh edges
	def gen_qm_msg(self):
		msg = ""
		for to, v in self.graph.items():
			for fr0m, e in v.items():
				if not e.shared:
					e.shared = True
					if msg:
						msg += " "
					msg += "%s:%s:%d" % (to, fr0m, e.rssi)
				if len(msg) > 50:
					break
			if len(msg) > 50:
				break
		return msg

	# Send QM packets to share learn graph edges
	def send_qm(self):
		msg = self.gen_qm_msg()
		if not msg:
			return

		pkt = Packet("QM", "", "QM", self.helper['max_ttl'](), msg)

		if MAPPER_VERBOSITY > 50:
			print("%s: rt publishing %s" % \
				(self.callsign, msg))

		self.helper['sendmsg'](pkt)
