#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys
from sim_packet import Packet

ROUTER_VERBOSITY=50

class Router:
	def __init__(self, callsign, helper):
		self.routes = []
		self.callsign = callsign
		self.edges = {}
		self.sent_edges = {}
		self.helper = helper
		self.routines = [ MeshFormation(self.callsign, self.helper) ]

	def learn(self, ident, ttl, path, last_hop_rssi):
		# Extract graph edges from breadcrumb path
		if not path:
			return

		if ttl >= 0:
			# path[0] is neighbor
			path = [ self.callsign ] + path

		if ROUTER_VERBOSITY > 90:
			print("%s rt: learning path %s ident %s ttl %d" \
				% (self.callsign, " < ".join(path), ident, ttl))

		for i in range(0, len(path) - 1):
			to = path[i]
			fr0m = path[i+1]
			# print("#### %s %s %s" % (str(path), to, fr0m))

			if to == fr0m:
				print("#### FATAL %s <- %s" % (to, fr0m))
				sys.exit(1)

			cost = 1000
			if i == 0:
				# Cost of adjacent node = -RSSI
				cost = -last_hop_rssi

			# FIXME cost not being propagated

			if to not in self.edges:
				self.edges[to] = {}
				self.sent_edges[to] = {}

			if fr0m not in self.edges[to]:
				self.edges[to][fr0m] = cost
				self.sent_edges[to][fr0m] = False
				if ROUTER_VERBOSITY > 50:
					print("%s rt: learnt edge %s < %s" % \
						(self.callsign, to, fr0m))

			elif self.edges[to][fr0m] > cost:
				self.edges[to][fr0m] = cost
				if ROUTER_VERBOSITY > 50:
					print("%s rt: reduced cost %s < %s" % \
						(self.callsign, to, fr0m))

		if ROUTER_VERBOSITY >= 50:
			learnt_edges = sum(len(v.keys()) for k, v in self.edges.items())
			total_edges = self.helper['total_edges']()
			pp = 100 * learnt_edges / total_edges
			print("%s rt knows %.1f%%" % (self.callsign, pp))
			# print("\tknows: ", self.edges)

	def prune(self, left_is_us, path):
		# Remove heading and trailing edges that we have already published
		# NOTE: assume that path was already learn()ed
		path_before = path[:]
		path = path[:]

		if ROUTER_VERBOSITY > 90:
			print("%s rt: pruning path %s" % (self.callsign, " < ".join(path)))

		if left_is_us:
			# Cannot prune at left because of guarantee that
			# path[0] == ourselves when ttl >= 0
			pass
		else:
			# Prune at left
			while len(path) >= 2:
				to = path[0]
				fr0m = path[1]
				if self.sent_edges[to][fr0m]:
					# Already sent, prune
					path = path[1:]
					if ROUTER_VERBOSITY > 90:
						print("%s rt: pruned edge %s < %s" % \
							(self.callsign, to, fr0m))
				else:
					break
	
		# Prune at right
		while len(path) >= 2:
			to = path[-2]
			fr0m = path[-1]
			if self.sent_edges[to][fr0m]:
				# Already sent, prune
				path = path[:-1]
				if ROUTER_VERBOSITY > 90:
					print("%s rt: pruned edge %s < %s" % \
						(self.callsign, to, fr0m))
			else:
				break
		
		if len(path) < 2:
			path = []

		if ROUTER_VERBOSITY > 90:
			if len(path_before) != len(path):
				print("\tbefore pruning: %s" % " < ".join(path_before))
				print("\tafter pruning: %s" % " < ".join(path))

		return path

	def sent(self, ident, ttl, path):
		if ROUTER_VERBOSITY > 60:
			print("%s rt: sent ttl %d ident %s path %s" % \
				(self.callsign, ttl, ident, " < ".join(path)))

		for i in range(0, len(path) - 1):
			self.sent_edges[path[i]][path[i + 1]] = True

	def handle_pkt(self, radio_rssi, pkt):
		# Handle mesh formation packet

		if pkt.to != "QM" or pkt.fr0m != "QM":
			return False

		msg = pkt.msg.upper().strip()
		if not msg:
			if ROUTER_VERBOSITY > 40:
				print("%s: Bad QM packet msg", self.callsign)
			return True

		# Parse message into a path
		path = msg.split("<")
		if ROUTER_VERBOSITY > 50:
			print("%s: rt recv path %s ttl %d ident %s" % \
				(self.callsign, "<".join(path), pkt.ttl, pkt.ident))

		self.learn(pkt.ident, pkt.ttl, path, radio_rssi)

		# Hop count control
		pkt = pkt.decrement_ttl()
		if pkt.ttl < -self.helper['max_ttl']():
			if ROUTER_VERBOSITY > 60:
				print("\tnot forwarding - ttl")
			return True

		# Only add ourselves to path if len(path) <= TTL
		if pkt.ttl >= 0:
			path = [ self.callsign ] + path

		# Prune parts of the route we've already broadcasted
		# but guarantee that path[0] = us when ttl >= 0
		path = self.prune(pkt.ttl >= 0, path)
		if len(path) < 2:
			if ROUTER_VERBOSITY > 90:
				print("\tnothing left after pruning")
			return True

		# Forward with updated path
		pkt = pkt.replace_msg("<".join(path))
		self.helper['sendmsg'](pkt)
		self.sent(pkt.ident, pkt.ttl, path)

		return True

	def get_first_hop(self, to):
		# TODO implement routing logic
		return ""

	def get_next_hop(self, to, via, fr0m):
		# TODO implement routing logic
		if via is None or via == "":
			return ""
		return None


loop = asyncio.get_event_loop()

class MeshFormation:
	def __init__(self, station, helper):
		async def probe():
			await asyncio.sleep(1 + random.random() * 5)
			while True:
				pkt = Packet("QM", "", "QM", helper['max_ttl'](), station)
				helper['sendmsg'](pkt)
				await asyncio.sleep(120 + random.random() * 60)
		loop.create_task(probe())
