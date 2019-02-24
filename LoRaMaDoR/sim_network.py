#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys
from sim_router import Router
from sim_packet import Packet

L3_VERBOSITY=50

MAX_TTL=0

def ttl(t):
	global MAX_TTL
	MAX_TTL = t

class Station:
	pending_pkts = []

	def __init__(self, callsign, radio):
		self.callsign = callsign.upper()
		self.recv_pkts = []
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

	def send(self, to, msg):
		# Called when we originate a packet
		ttl = MAX_TTL
		if to == "QB":
			ttl = 1
		pkt = Packet(to, "", self.callsign, ttl, msg)
		self.sendmsg(pkt)

	def sendmsg(self, pkt):
		Station.pending_pkts.append(pkt)
		print("%s => %s" % (self.callsign, pkt))
		self._forward(None, pkt, True)

	def recv(self, pkt):
		# Called when we are the recipient of a packet
		if pkt in Station.pending_pkts:
			Station.pending_pkts.remove(pkt)
		print("%s <= %s" % (self.callsign, pkt))

	def radio_recv(self, rssi, pkt):
		# Got a packet from radio
		if L3_VERBOSITY > 80:
			print("%s <= rssi %s pkt " % (self.callsign, pkt))

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
			self.recv_pkts.append(pkt)
			self.radio.send(self.callsign, pkt)
			return

		# Offer packet to router, drop if fully handled by router
		if self.router.handle_pkt(radio_rssi, pkt):
			self.recv_pkts.append(pkt)
			return

		# Discard received duplicates
		if pkt in self.recv_pkts:
			if L3_VERBOSITY > 80:
				print("%s <= recv dup %s" % (self.callsign, pkt))
			return
		self.recv_pkts.append(pkt)

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
			if L3_VERBOSITY > 90:
				print("%s: dropped %s" % (self.callsign, pkt))
			return

		if pkt.via:
			# Active routing
			if pkt.via != self.callsign:
				# Not for us to forward
				if L3_VERBOSITY > 80:
					print("%s: not forwarding %s" % (self.callsign, pkt))
					return

			# Find next hop
			next_hop = self.router.get_next_hop(pkt)
			if not next_hop:
				if L3_VERBOSITY > 50:
					print("%s: no route for %s" % (self.callsign, pkt))
				return

			pkt = pkt.update_via(next_hop)

			if L3_VERBOSITY > 50:
				print("%s: forwarding %s" % (self.callsign, pkt))

		if not pkt.via:
			# Diffusion routing, forwarding blindly
			if L3_VERBOSITY > 60:
				print("%s: forwarding %s" % (self.callsign, pkt))

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
				station.send("QB", "beacon")
				await asyncio.sleep(30 + random.random() * 60)
		loop.create_task(beacon())


def run():
	async def list_pending_pkts():
		while True:
			await asyncio.sleep(120)
			print("Packets pending delivery:", Station.pending_pkts)
	loop.create_task(list_pending_pkts())

	loop.run_forever()
	loop.close()
