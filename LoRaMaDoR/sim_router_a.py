#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time
from sim_packet import Packet

ROUTER_VERBOSITY = 100

CAN_DIFFUSE_UNKNOWN = True
CAN_DIFFUSE_NOROUTE = True

# Base route class. Can route packets, but does not learn routes

class AbstractRouter:
	def __init__(self, callsign, helper):
		self.callsign = callsign
		self.edges = {}
		self.sent_edges = {}
		self.helper = helper
		self.cache = {}

		async def cache_expire():
			while True:
				await asyncio.sleep(120 + random.random() * 60)
				self.cache_expire()


		loop = asyncio.get_event_loop()
		loop.create_task(cache_expire())

	def cache_expire():
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
		
	# Use some incoming packets to discover routing
	# Returns True if the packet is exhausted (e.g. routing protocol packets)
	# and does not need further handling

	def handle_pkt(self, radio_rssi, pkt):
		return False

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
