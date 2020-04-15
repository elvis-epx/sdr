#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, time, string
from sim_packet import Packet
from sim_handler import app_handlers
from sim_modifier import fwd_modifiers

VERBOSITY=51

class Beacon:
	def __init__(self, station):
		async def beacon():
			while True:
				await asyncio.sleep(600 * (0.5 + random.random()))
				msg = ''.join(random.choice(string.ascii_lowercase + string.digits) \
					for _ in range(3))
				station.send("QB", {}, msg)
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
		self.adjacent_stations = {}
		self.traffic_gens = [ Beacon(self) ]
		self.radio = radio
		radio.attach(callsign, self)

		loop.create_task(self.known_pkts_clean())
		loop.create_task(self.pkt_id_reset())
		loop.create_task(self.adjacent_stations_clean())

	async def known_pkts_clean(self):
		while True:
			await asyncio.sleep(60)
			remove_list = []
			cutoff = time.time() - 600
			for k, v in self.known_pkts.items():
				if v < cutoff:
					remove_list.append(k)
			for k in remove_list:
				if VERBOSITY > 10:
					print("Forgotten packet %s" % k)
				del self.known_pkts[k]

	async def adjacent_stations_clean(self):
		while True:
			await asyncio.sleep(600)
			remove_list = []
			cutoff = time.time() - 3600
			for k, v in self.adjacent_stations.items():
				if v["last_q"] < cutoff:
					remove_list.append(k)
			for k in remove_list:
				if VERBOSITY > 10:
					print("Removed adjacent station %s" % k)
				del self.adjacent_stations[k]

	async def pkt_id_reset(self):
		while True:
			await asyncio.sleep(1200)
			self.last_pkt_id = 0
			Station.last_pkt_id = 0

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
		print("\n%s => %s\n" % (self.callsign, pkt))
		async def asend():
			self._forward(None, pkt, True)
		loop.create_task(asend())

	# Called when we are the final recipient of a packet
	def recv(self, pkt):
		if pkt.signature() in Station.dbg_pend_deliv:
			del Station.dbg_pend_deliv[pkt.signature()]
		print("\n%s <= %s\n" % (self.callsign, pkt))

		# Automatic application protocol handlers
		for handler in app_handlers:
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
			self.known_pkts[pkt.signature()] = time.time()

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
		self.known_pkts[pkt.signature()] = time.time()

		if pkt.to == self.callsign:
			# We are the final destination
			self.recv(pkt)
			return
		elif pkt.to in ("QB", "QC"):
			# We are just one of the destinations
			if "R" not in pkt.params:
				if pkt.fr0m not in self.adjacent_stations and VERBOSITY > 50:
					print("%s: discovered neighbour %s" % (self.callsign, pkt.fr0m))
				self.adjacent_stations[pkt.fr0m] = \
					{"last_q": time.time(), "rssi": radio_rssi}
			self.recv(pkt)

		# Forward packet modifiers
		# They can add params and/or change msg
		for mod in fwd_modifiers:
			if mod.match(pkt):
				more_params, msg = mod.handle(self, pkt)
				if msg is not None:
					pkt = pkt.change_msg(msg)
				if more_params:
					for k, v in more_params.items():
						pkt = pkt.append_param(k, v)

		# Diffusion routing
		delay = random.random() * len(pkt.encode()) * 8 * 2 * (1 + len(self.adjacent_stations)) / 1400
		if VERBOSITY > 50:
			print("%s: relaying with delay %d: %s" % (self.callsign, delay * 1000, pkt))

		async def asend():
			await asyncio.sleep(delay)
			self.radio.send(self.callsign, pkt.encode())
		loop.create_task(asend())

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
