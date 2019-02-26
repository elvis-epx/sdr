#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time
from sim_packet import Packet
from sim_router_a import AbstractRouter, ROUTER_VERBOSITY

# This router uses "breadcrumb" packets to discover the network graph
# Packets with QM pseudo-addr destination are diffused, each node adds
# itself to the message, in the end revealing the packet trajectory
# and therefore a set of viable graph edges.
# QM packets are added nodes until ttl = 0, but they are diffused further
# until ttl = -MAX_TTL because graphs may be one-way, the extended diffusion
# allows the edges to "reach back" -- think about a ring network of 5 nodes
# and TTL=3, A can only learn about D if the QM packet can go D > E > A.

class Router(AbstractRouter):
	def __init__(self, callsign, helper):
		super().__init__(callsign, helper)

	# Extract graph edges from breadcrumb path

	def learn(self, ident, ttl, path, last_hop_rssi):
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

	# Remove heading and trailing edges that we have already published
	# NOTE: assume that path was already learn()ed

	def prune(self, left_is_us, path):
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

	# Mark the edges of this path as sent

	def sent(self, ident, ttl, path):
		if ROUTER_VERBOSITY > 60:
			print("%s rt: sent ttl %d ident %s path %s" % \
				(self.callsign, ttl, ident, " < ".join(path)))

		for i in range(0, len(path) - 1):
			self.sent_edges[path[i]][path[i + 1]] = True

	# Use some incoming packets to discover routing
	# Returns True if the packet is exhausted (e.g. routing protocol packets)
	#  and does not need further handling

	def handle_pkt(self, radio_rssi, pkt):

		if pkt.to == "QB" and pkt.fr0m != "QB" and pkt.fr0m != self.callsign:
			# Beacon packet from neighbor
			kind = "QB"
			msg = pkt.fr0m.strip()
		elif pkt.to == "QM" and pkt.fr0m == "QM":
			# QM packet, sent by another router
			kind = "QM"
			msg = pkt.msg.strip()
		else:
			return False

		if not msg:
			if ROUTER_VERBOSITY > 40:
				print("%s: Bad QM/QB path %s", (self.callsign, msg))
			return kind == "QM"

		path = msg.strip().upper().split("<")

		if ROUTER_VERBOSITY > 50:
			print("%s: rt recv path %s ttl %d ident %s" % \
				(self.callsign, "<".join(path), pkt.ttl, pkt.ident))

		self.learn(pkt.ident, pkt.ttl, path, radio_rssi)

		if kind == "QB":
			# Create new QM packet
			pkt = Packet("QM", "", "QM", self.helper['max_ttl'](), self.callsign)

		pkt = pkt.decrement_ttl()
		if pkt.ttl < -self.helper['max_ttl']():
			if ROUTER_VERBOSITY > 60:
				print("\tnot forwarding - max hop count")
			return kind == "QM"

		# Only add ourselves to path if len(path) <= TTL
		if pkt.ttl >= 0:
			path = [ self.callsign ] + path

		# Prune parts of the route we've already broadcasted
		# but guarantee that path[0] = us when ttl >= 0
		path = self.prune(pkt.ttl >= 0, path)
		if len(path) < 2:
			if ROUTER_VERBOSITY > 90:
				print("\tnothing left after pruning")
			return kind == "QM"

		# Update pkt.msg and send
		pkt = pkt.replace_msg("<".join(path))
		self.helper['sendmsg'](pkt)
		self.sent(pkt.ident, pkt.ttl, path)

		return kind == "QM"
