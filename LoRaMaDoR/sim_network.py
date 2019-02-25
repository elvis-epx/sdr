#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time, string
from sim_router import Router
from sim_packet import Packet

VERBOSITY=80

MAX_TTL=0

def ttl(t):
	global MAX_TTL
	MAX_TTL = t

class Station:
	all_callsigns = []
	dbg_pending_delivery_pkts = {}

	def get_all_callsigns():
		return Station.all_callsigns[:]

	def __init__(self, callsign, radio):
		self.callsign = callsign.upper()
		if self.callsign not in Station.all_callsigns:
			Station.all_callsigns.append(self.callsign)
		self.already_received_pkts = {}
		self.traffic_gens = []
		self.radio = radio

		# For debugging purposes
		def total_edges():
			return self.radio.active_edges()
		# For router usage
		def sendmsg(pkt):
			return self.sendmsg(pkt)
		def max_ttl():
			return MAX_TTL
		helper = {"total_edges": total_edges, "sendmsg": sendmsg, "max_ttl": max_ttl}

		self.router = Router(self.callsign, helper)
		radio.attach(callsign, self)

		self.add_traffic_gen(Beacon)

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
				if VERBOSITY > 90:
					print("%s: expired memory of %d pkts" % (self.callsign, len(old)))
		loop.create_task(cleanup())

	def send(self, to, msg):
		# Called when we originate a packet
		ttl = MAX_TTL
		if to == "QB":
			ttl = 1
		via = self.router.get_first_hop(to)
		if via is None:
			if VERBOSITY > 40:
				print("%s: send: cannot route %s" % (self.callsign, str(pkt)))
			return
		pkt = Packet(to, via, self.callsign, ttl, msg)
		self.sendmsg(pkt)

	def sendmsg(self, pkt):
		Station.dbg_pending_delivery_pkts[pkt.tag] = pkt
		print("%s => %s" % (self.callsign, pkt))
		self._forward(None, pkt, True)

	def recv(self, pkt):
		# Called when we are the recipient of a packet
		if pkt.tag in Station.dbg_pending_delivery_pkts:
			del Station.dbg_pending_delivery_pkts[pkt.tag]
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

		if from_us:
			# We are the origin
			if pkt.to in ("QL", "Q", self.callsign):
				# Loopback
				self.recv(pkt)
				return
			# Annotate to detect duplicates
			self.already_received_pkts[pkt.meaning()] = (pkt, time.time())
			self.radio.send(self.callsign, pkt)
			return

		# Offer packet to router, drop if fully handled by router
		if self.router.handle_pkt(radio_rssi, pkt):
			if pkt.tag in Station.dbg_pending_delivery_pkts:
				del Station.dbg_pending_delivery_pkts[pkt.tag]
			self.already_received_pkts[pkt.meaning()] = (pkt, time.time())
			return

		# Discard received duplicates
		if pkt.meaning() in self.already_received_pkts:
			if VERBOSITY > 80:
				print("%s DUP recv %s" % (self.callsign, pkt))
			return
		self.already_received_pkts[pkt.meaning()] = (pkt, time.time())

		if pkt.to in (self.callsign, "QB"):
			# We are the final destination
			# QB one-hop policy is enforced, too
			self.recv(pkt)
			return

		if pkt.to in ("QF"):
			# We are one of many recipients
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

		if pkt.via:
			# Explicit routing
			if pkt.via != self.callsign:
				# Not our problem
				if VERBOSITY > 80:
					print("%s: ignoring %s" % (self.callsign, pkt))
					return

			# Find next hop
			next_hop = self.router.get_next_hop(pkt.to, pkt.via, pkt.fr0m)
			if next_hop is None:
				if VERBOSITY > 50:
					print("%s: no route for %s" % (self.callsign, pkt))
				return

			pkt = pkt.update_via(next_hop)

			if VERBOSITY > 50:
				print("%s: relaying %s" % (self.callsign, pkt))

		if not pkt.via:
			# Diffusion routing, forwarding blindly
			if VERBOSITY > 50:
				print("%s: d-relaying %s" % (self.callsign, pkt))

		# Send away
		self.radio.send(self.callsign, pkt)

	def add_traffic_gen(self, klass):
		self.traffic_gens.append(klass(self))
		return self


loop = asyncio.get_event_loop()

class Beacon:
	def __init__(self, station):
		async def beacon():
			await asyncio.sleep(random.random() * 1)
			while True:
				msg = ''.join(random.choice(string.ascii_lowercase + string.digits) \
					for _ in range(3))
				station.send("QB", msg)
				await asyncio.sleep(30 + random.random() * 60)
		loop.create_task(beacon())


def run():
	async def list_pending_pkts():
		while True:
			await asyncio.sleep(30)
			print("Packets pending delivery:", Station.dbg_pending_delivery_pkts)
	loop.create_task(list_pending_pkts())

	loop.run_forever()
	loop.close()
