#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time, string
from sim_packet import Packet
from sim_handler import final_handlers, interm_handlers

VERBOSITY=50

class Beacon:
	def __init__(self, station):
		async def beacon():
			await asyncio.sleep(10 * (0.5 + random.random()))
			while True:
				msg = ''.join(random.choice(string.ascii_lowercase + string.digits) \
					for _ in range(3))
				station.send("QB", {}, msg)
				await asyncio.sleep(600 * (0.5 + random.random()))
		loop.create_task(beacon())

class Station:
	dbg_all_callsigns = []
	dbg_pend_deliv = {}
	dbg_pend_deliv_ant = {}
	last_pkt_id = 0 # in class to make simulator easier

	def get_all_callsigns():
		return Station.dbg_all_callsigns[:]

	def __init__(self, callsign, radio):
		self.callsign = callsign.upper()
		if self.callsign not in Station.dbg_all_callsigns:
			Station.dbg_all_callsigns.append(self.callsign)
		self.known_pkts = {}
		self.traffic_gens = [ Beacon(self) ]
		self.radio = radio
		radio.attach(callsign, self)

		async def known_pkts_clean():
			while True:
				await asyncio.sleep(600)
				self.known_pkts = {}

		async def pkt_id_reset():
			while True:
				await asyncio.sleep(1200)
				# self.last_pkt_id = 0

		loop.create_task(known_pkts_clean())
		loop.create_task(pkt_id_reset())

	def get_pkt_id(self):
		Station.last_pkt_id += 1
		return Station.last_pkt_id

	# Called when we originate a packet
	def send(self, to, params, msg):
		pkt = Packet(to, self.callsign, self.get_pkt_id(), params, msg)
		self.sendmsg(pkt)

	# Generic packet sending procedure
	def sendmsg(self, pkt):
		if pkt.to != "UNKNOWN":
			Station.dbg_pend_deliv[pkt.signature()] = pkt
		print("%s => %s" % (self.callsign, pkt))
		async def asend():
			self._forward(None, pkt, True)
		loop.create_task(asend())

	# Called when we are the final recipient of a packet
	def recv(self, pkt):
		if pkt.signature() in Station.dbg_pend_deliv:
			del Station.dbg_pend_deliv[pkt.signature()]
		print("%s <= %s" % (self.callsign, pkt))
		# Automatic handlers
		for handler in final_handlers:
			if handler.match(pkt):
				handler(self, pkt)
				return

	# Generic packet receivign procedure
	def radio_recv(self, rssi, string_pkt):
		pkt = Packet.decode(string_pkt)
		if not pkt:
			if VERBOSITY > 10:
				print("Invalid packet received: %s" % string_pkt)
			return
		if VERBOSITY > 80:
			print("%s <= rssi %d pkt %s" % (self.callsign, rssi, pkt))
		self._forward(rssi, pkt, False)

	# Handle packet forwarding
	def _forward(self, radio_rssi, pkt, we_are_origin):

		# Sanity check
		if not pkt.to or not pkt.fr0m:
			print("%s: bad pkt %s" % (self.callsign, pkt))
			return

		if we_are_origin:
			if pkt.to in ("QL", self.callsign):
				# Destination is loopback
				self.recv(pkt)
				return

			# Annotate to detect duplicates
			self.known_pkts[pkt.signature()] = pkt

			# Transmit
			self.radio.send(self.callsign, pkt.encode())
			return
	
		# Packet originated from us but received via radio = loop
		if pkt.fr0m == self.callsign:
			if VERBOSITY > 80:
				print("%s *loop* %s" % (self.callsign, pkt))
			return

		# Discard received duplicates
		if pkt.signature() in self.known_pkts:
			if VERBOSITY > 80:
				print("%s *dup* %s" % (self.callsign, pkt))
			return
		self.known_pkts[pkt.signature()] = pkt

		# Intermediate handlers / packet modifiers
		# They can add params and/or change msg
		for handler in interm_handlers:
			if handler.match(pkt):
				more_params, msg = handler.handle(self, pkt)
				pkt = pkt.change_msg(msg)
				for k, v in more_params:
					pkt = pkt.append_param(k, v)
				break

		if pkt.to == self.callsign:
			# We are the final destination
			self.recv(pkt)
			return
		elif pkt.to in ("QB", "QC"):
			# We are just one of the destinations
			self.recv(pkt)
			pkt = pkt.append_param("R", None)

		# Diffusion routing
		if VERBOSITY > 50:
			print("%s: relaying %s" % (self.callsign, pkt))
		self.radio.send(self.callsign, pkt.encode())

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
					print("%s not delivered in 30s" % k)
					sys.exit(1)
			Station.dbg_pend_deliv_ant = Station.dbg_pend_deliv.copy()

	loop.create_task(list_pending_pkts())
	loop.run_forever()
	loop.close()
