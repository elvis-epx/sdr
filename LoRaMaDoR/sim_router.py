#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time
from sim_packet import Packet

ROUTER_VERBOSITY = 100

CAN_DIFFUSE_UNKNOWN = True
CAN_DIFFUSE_NOROUTE = True

class Router:
	def __init__(self, callsign, helper):
		self.callsign = callsign
		self.edges = {}
		self.sent_edges = {}
		self.helper = helper
		self.cache = {}

		async def cache_expire():
			while True:
				await asyncio.sleep(120 + random.random() * 60)
				if ROUTER_VERBOSITY > 90:
					print("%s rt: cache expiration control" % self.callsign)

				now = time.time()
				expired = []

				for to, item in self.cache.items():
					via, cost, timestamp = item
					if (now - timestamp) > 120:
						expired.append(to)
					if ROUTER_VERBOSITY > 90:
						print("%s rt: expiring cached %s < %s < %s" % \
							(self.callsign, to, via, self.callsign))
				for to in expired:
					del self.cache[to]

		loop = asyncio.get_event_loop()
		loop.create_task(cache_expire())

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
		# Use some incoming packets to discover routing
		# Returns True if the packet is exhausted (e.g. routing protocol packets)
		#  and does not need further handling

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

	# Calculate next 'via' station.
	# Returns: "" to resort to diffusion routing
	#          None if packet should not be repeated

	def get_next_hop(self, to):
		repeater, cost = self._get_next_hop(to, (to, ))
		if repeater == self.callsign:
			repeater = "QB"
		return repeater

	def _get_next_hop(self, to, path):
		if to == "QF" or to == "QB" or to == "QM":
			# these always go by diffusion
			return "", 0
		elif to and to[0] == "Q":
			raise Exception("%s rt: asked route to %s" % (self.callsign, to))
		elif to == self.callsign:
			# should not happen
			raise Exception("%s rt: asked route to itself" % self.callsign)

		recursion = "=|" * (len(path) - 1)
		if recursion:
			recursion += " "

		if to in self.cache:
			via, cost, _ = self.cache[to]
			if ROUTER_VERBOSITY > 90:
				print("%s%s rt: using cached %s < %s < %s" % \
					(recursion, self.callsign, to, via, self.callsign))
			return via, cost

		if to not in self.edges:
			# Unknown destination
			if CAN_DIFFUSE_UNKNOWN:
				if ROUTER_VERBOSITY > 90:
					print("%s%s rt: dest %s unknown, use diffusion" % \
						(recursion, self.callsign, to))
				return "", 999999999
			if ROUTER_VERBOSITY > 90:
				print("%s%s rt: dest %s unknown, cannot route" % \
					(recursion, self.callsign, to))
			return None, 999999999

		if self.callsign in self.edges[to]:
			# last hop, no actual routing
			return to, self.edges[to][self.callsign]

		if ROUTER_VERBOSITY > 90:
			print("%s%s rt: looking for route %s < %s" % \
				(recursion, self.callsign, to, self.callsign))

		# Try to find cheapest route, walking backwards from 'to'
		best_cost = 999999999
		best_via = None
		for penultimate, pcost in self.edges[to].items():
			if ROUTER_VERBOSITY > 90:
				print("%s \tlooking for route to %s" % (recursion, penultimate))

			if penultimate in path:
				# would create a loop
				if ROUTER_VERBOSITY > 90:
					print("%s \t\tloop %s" % (recursion, str(path)))
				continue

			via, cost = self._get_next_hop(penultimate, (penultimate,) + path)
			cost += pcost

			if not via:
				print("%s \t\tno route" % recursion)
				continue

			if ROUTER_VERBOSITY > 90:
				print("%s \t\tcandidate %s < %s < %s < %s cost %d" % \
					(recursion, to, penultimate, via, self.callsign, cost))

			if not best_via or cost < best_cost:
				best_via = via
				best_cost = cost

		if not best_via:
			# Did not find route
			if CAN_DIFFUSE_NOROUTE:
				if ROUTER_VERBOSITY > 90:
					print("%s \troute not found, using diffusion" % recursion)
				return "", 999999999
			if ROUTER_VERBOSITY > 90:
				print("%s \troute not found, giving up" % recursion)
			return None, 999999999

		if ROUTER_VERBOSITY > 90:
			print("%s \tadopted %s < %s < %s cost %d" % (recursion, to, via, self.callsign, best_cost))

		if best_via:
			self.cache[to] = (best_via, cost, time.time())
			if ROUTER_VERBOSITY > 90:
				print("%s%s rt: caching %s < %s < %s cost %d" % \
					(recursion, self.callsign, to, best_via, self.callsign, cost))

		return best_via, best_cost
