#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys

VERBOSITY=50
SPEED=1400.0 # bps

loop = asyncio.get_event_loop()

class Radio:
	dbg_pkts_sent = 0
	dbg_bits_sent = 0

	def __init__(self):
		self.edges = {}
		self.stations = {}
		async def transmitted():
			while True:
				runtime = 30
				await asyncio.sleep(runtime)
				print("########### radio: sent %d pkts %d bits %d bps" % 
					(Radio.dbg_pkts_sent, Radio.dbg_bits_sent,
					Radio.dbg_bits_sent / runtime))
				Radio.dbg_pkts_sent = 0
				Radio.dbg_bits_sent = 0
		loop.create_task(transmitted())

	def active_edges(self):
		n = 0
		for _, v in self.edges.items():
			for __, rssi in v.items():
				if rssi is not None:
					n += 1
		return n

	def edge(self, to, fr0m, rssi):
		if fr0m not in self.edges:
			self.edges[fr0m] = {}
		self.edges[fr0m][to] = rssi

	def biedge(self, to, fr0m, rssi1, rssi2):
		self.edge(to, fr0m, rssi1)
		self.edge(fr0m, to, rssi2)

	def attach(self, callsign, station):
		self.stations[callsign] = station

	def send(self, fr0m, pkt_string):
		Radio.dbg_pkts_sent += 1
		bits = 8 * len(pkt_string)
		Radio.dbg_bits_sent += bits

		if fr0m not in self.edges or not self.edges[fr0m]:
			print("radio %s: nobody listens to me", fr0m)
			return

		for dest, rssi in self.edges[fr0m].items():
			if rssi is None:
				if VERBOSITY > 80:
					print("radio %s: not bcasting to %s" % \
						(fr0m, dest))
				continue
			else:
				if VERBOSITY > 70:
					print("radio %s: bcasting %s " % \
						(fr0m, dest))

			async def asend(d, r, ps):
				await asyncio.sleep((bits / SPEED) * (1 + 0.2 * random.random()))
				self.stations[d].radio_recv(r, ps)

			loop.create_task(asend(dest, rssi, pkt_string))
