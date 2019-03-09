#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time
from sim_packet import Packet

ROUTER_VERBOSITY = 60

CAN_DIFFUSE_UNKNOWN = False
CAN_DIFFUSE_NOROUTE = False

class Edge:
	def __init__(self, cost, expiry):
		self.cost = cost 
		self.expiry = expiry

class Router:
	def __init__(self, callsign):
		self.callsign = callsign
		self.graph = {}

		async def run_expire():
			while True:
				await asyncio.sleep(60)
				self.expire()

		loop = asyncio.get_event_loop()
		loop.create_task(run_expire())

	def add_edge(self, to, fr0m, rssi, expiry):
		if to not in self.graph:
			self.graph[to] = {}

		# Cost formula #########
		cost = -rssi

		self.graph[to][fr0m] = Edge(cost, expiry)
				
	def expire(self):
		now = time.time()
		expired = []

		for to, allfrom in self.graph.items():
			for fr0m, item in allfrom.items():
				if item.expiry < now:
					expired.append((to, fr0m))
					if ROUTER_VERBOSITY > 90:
						print("%s rt: expiring edge %s < %s (%d)" % \
							(self.callsign, to, fr0m, item.expiry))

		for to, fr0m in expired:
			del self.graph[to][fr0m]
		
	# Calculate next 'via' station.
	# Returns: "" to resort to diffusion routing
	#          None if packet should not be repeated

	def get_next_hop(self, to):
		repeater, cost = self._get_next_hop(to, (to, ))
		if repeater == self.callsign:
			repeater = "QB"
		else:
			if ROUTER_VERBOSITY > 60:
				print("%s: route to %s via %s cost %d" % \
					(self.callsign, to, repeater, cost))
		return repeater

	def _get_next_hop(self, to, path):
		if to in ("QF", "QB", "QM", "QN"):
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

		if to not in self.graph:
			# Unknown destination
			if CAN_DIFFUSE_UNKNOWN:
				if ROUTER_VERBOSITY > 50:
					print("%s%s rt: dest %s unknown, use diffusion" % \
						(recursion, self.callsign, to))
				return "", 999999999
			if ROUTER_VERBOSITY > 50:
				print("%s%s rt: dest %s unknown, cannot route" % \
					(recursion, self.callsign, to))
			return None, 999999999

		if self.callsign in self.graph[to]:
			# last hop, no actual routing
			return to, self.graph[to][self.callsign].cost

		if ROUTER_VERBOSITY > 90:
			print("%s%s rt: looking for route %s < %s" % \
				(recursion, self.callsign, to, self.callsign))

		# Try to find cheapest route, walking backwards from 'to'
		best_cost = 999999999
		best_via = None
		for penultimate, edge in self.graph[to].items():
			if ROUTER_VERBOSITY > 90:
				print("%s \tlooking for route to %s" % (recursion, penultimate))

			if penultimate in path:
				# would create a loop
				if ROUTER_VERBOSITY > 90:
					print("%s \t\tloop %s" % (recursion, str(path)))
				continue

			via, cost = self._get_next_hop(penultimate, (penultimate,) + path)
			cost += edge.cost

			if not via:
				if ROUTER_VERBOSITY > 90:
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

		return best_via, best_cost
