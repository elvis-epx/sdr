#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time, string
from sim_packet import Packet

VERBOSITY=80

MAX_TTL=0

def ttl(t):
	global MAX_TTL
	MAX_TTL = t

class Station:
	all_callsigns = []
	dbg_pend_deliv = {}
	dbg_pend_deliv_ant = {}

	def get_all_callsigns():
		return Station.all_callsigns[:]

	def __init__(self, callsign, radio, router_class, mapper_class):
		self.callsign = callsign.upper()
		if self.callsign not in Station.all_callsigns:
			Station.all_callsigns.append(self.callsign)
		self.already_received_pkts = {}
		self.traffic_gens = []
		self.radio = radio
		self.router = router_class(self.callsign)

		# For debugging purposes
		def total_edges():
			return self.radio.active_edges()
		# For route mapper usage
		def sendmsg(pkt):
			return self.sendmsg(pkt)
		def max_ttl():
			return MAX_TTL
		def send_to_router(to, fr0m, rssi, expiry):
			return self.router.add_edge(to, fr0m, rssi, expiry)

		helper = {
			"total_edges": total_edges,
			"sendmsg": sendmsg,
			"max_ttl": max_ttl,
			"send_to_router": send_to_router
		}

		self.mapper = mapper_class(self.callsign, helper)

		radio.attach(callsign, self)

		async def cleanup():
			while True:
				await asyncio.sleep(60)
				now = time.time()
				old = []
				for k, v in self.already_received_pkts.items():
					if (now - v[1]) > 120:
						old.append(k)
				for k in old:
					del self.already_received_pkts[k]
				if VERBOSITY > 0:
					print("%s: expired memory of %d pkts" % (self.callsign, len(old)))
		loop.create_task(cleanup())

	def send(self, to, msg):
		# Called when we originate a packet
		ttl = MAX_TTL
		if to in ("QB", "QN"):
			ttl = 1
		via = self.router.get_next_hop(to)
		if via is None:
			if VERBOSITY > 40:
				print("%s: send: no route to %s" % (self.callsign, to))
			return
		pkt = Packet(to, via, self.callsign, ttl, msg)
		self.sendmsg(pkt)

	def sendmsg(self, pkt):
		Station.dbg_pend_deliv[pkt.tag] = pkt
		print("%s => %s" % (self.callsign, pkt))
		async def asend():
			self._forward(None, pkt, True)
		loop.create_task(asend())

	def recv(self, pkt):
		# Called when we are the recipient of a packet
		if pkt.tag in Station.dbg_pend_deliv:
			del Station.dbg_pend_deliv[pkt.tag]
		print("%s <= %s" % (self.callsign, pkt))

	def radio_recv(self, rssi, pkt):
		# Got a packet from radio
		if VERBOSITY > 80:
			print("%s <= rssi %d pkt %s" % (self.callsign, rssi, pkt))

		# Level 3 handling
		self._forward(rssi, pkt, False)

	def _forward(self, radio_rssi, pkt, from_us):
		# Handle the packet in L3

		# Sanity check
		if not pkt.to or not pkt.fr0m:
			print("%s: bad pkt %s" % (self.callsign, pkt))
			return

		# Are we the origin?
		if from_us:
			# Destination is loopback?
			if pkt.to in ("QL", "Q", self.callsign):
				self.recv(pkt)
				return
			# Annotate to detect duplicates
			self.already_received_pkts[pkt.meaning()] = (pkt, time.time())
			# Transmit
			self.radio.send(self.callsign, pkt)
			return

		# Offer packet to mapper, drop if fully handled by mapper
		if self.mapper.handle_pkt(radio_rssi, pkt):
			if pkt.tag in Station.dbg_pend_deliv:
				del Station.dbg_pend_deliv[pkt.tag]
			self.already_received_pkts[pkt.meaning()] = (pkt, time.time())
			return

		# Discard received duplicates
		if pkt.meaning() in self.already_received_pkts:
			if VERBOSITY > 80:
				print("%s DUP recv %s" % (self.callsign, pkt))
			return
		self.already_received_pkts[pkt.meaning()] = (pkt, time.time())

		# Are we the final destination?
		if pkt.to in (self.callsign, "QB", "QN"):
			self.recv(pkt)
			return

		# Are we one of the recipients?
		if pkt.to in ("QF"):
			self.recv(pkt)

		self._repeat(pkt)
		return

	def _repeat(self, pkt):
		######## Repeater logic

		# Hop count control
		pkt = pkt.decrement_ttl()
		if pkt.ttl <= 0:
			if VERBOSITY > 90:
				print("%s: dropped %s" % (self.callsign, pkt))
			return

		if not pkt.via:
			# Diffusion routing
			if VERBOSITY > 50:
				print("%s: d-relaying %s" % (self.callsign, pkt))
			self.radio.send(self.callsign, pkt)
			return

		# Explicit routing

		if pkt.via != self.callsign:
			# Not our responsability to repeat
			if VERBOSITY > 80:
				print("%s: not repeating %s" % (self.callsign, pkt))
			return

		# Find next hop
		next_hop = self.router.get_next_hop(pkt.to)
		# next hop can be "", None, or station
		# the router decides whether deny route or resort to diffusion
		if next_hop is None:
			if VERBOSITY > 50:
				print("%s: no route for %s" % (self.callsign, pkt))
			return

		pkt = pkt.update_via(next_hop)

		if VERBOSITY > 50:
			print("%s: relaying %s" % (self.callsign, pkt))

		# Send away
		self.radio.send(self.callsign, pkt)

	def add_traffic_gen(self, klass):
		self.traffic_gens.append(klass(self))
		return self


loop = asyncio.get_event_loop()

def run():
	async def list_pending_pkts():
		while True:
			await asyncio.sleep(30)
			print("Packets pending delivery:", Station.dbg_pend_deliv)
			for k in Station.dbg_pend_deliv_ant:
				if k in Station.dbg_pend_deliv:
					print("%d not delivered in 30s" % k)
					sys.exit(1)
			Station.dbg_pend_deliv_ant = Station.dbg_pend_deliv

	loop.create_task(list_pending_pkts())
	loop.run_forever()
	loop.close()
