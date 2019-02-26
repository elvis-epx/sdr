#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time
from sim_packet import Packet
from sim_router_a import AbstractRouter, ROUTER_VERBOSITY

# FIXME

class Router(AbstractRouter):
	def __init__(self, callsign, helper):
		super().__init__(callsign, helper)
		# FIXME expire edges (possibly in superclass, chk breadcrumb)

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

	def _parse_qm(self, msg):
		info = msg.strip().upper().split(":")
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

	def handle_pkt(self, radio_rssi, pkt):
		if pkt.to == "QB" and pkt.fr0m != "QB" and pkt.fr0m != self.callsign:
			# Beacon packet from neighbor
			print("%s rt: got QB pkt %s" % (self.callsign, pkt))
			kind = "QB"
			to = self.callsign
			fr0m = pkt.fr0m
			rssi = radio_rssi
		elif pkt.to == "QM" and pkt.fr0m == "QM":
			# QM packet, sent by another router
			print("%s rt: got QM pkt %s" % (self.callsign, pkt))
			kind = "QM"
			to, fr0m, rssi = self._parse_qm(pkt.msg)
			if to is None:
				if ROUTER_VERBOSITY > 40:
					print("%s: Bad QM msg %s", (self.callsign, pkt.msg))
				return False
		else:
			return False

		self.learn(to, fr0m, rssi)

		# Has this edge information been diffused already?
		if self.sent_edges[to][fr0m]:
			return kind == "QM"

		if kind == "QB":
			# Create new QM packet to diffuse this edge
			msg = "%s:%s:%.1f" % (to, fr0m, rssi)
			pkt = Packet("QM", "", "QM", self.helper['max_ttl'](), msg)

		pkt = pkt.decrement_ttl()
		if pkt.ttl < -self.helper['max_ttl']():
			if ROUTER_VERBOSITY > 60:
				print("\tmax hop count")
			return kind == "QM"

		if ROUTER_VERBOSITY > 50:
			print("%s: rt diffusing %s < %s rssi %f ttl %d ident %s" % \
				(self.callsign, to, fr0m, rssi, pkt.ttl, pkt.ident))

		self.helper['sendmsg'](pkt)
		self.sent_edges[to][fr0m] = True

		return kind == "QM"
