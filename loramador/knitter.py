#!/usr/bin/env python3

import random, math, asyncio

loop = asyncio.get_event_loop()

class Packet:
	last_ident = 0

	def __init__(self, to, via, fr0m, data):
		self.to = to.upper()
		self.via = to.upper()
		self.fr0m = fr0m.upper()

		self.maxhops = 10
		if to == "QB":
			self.maxhops = 1
		self.hopped = 0
		Packet.last_ident += 1
		self.data = ("%d" % Packet.last_ident) + " " + data

class Radio:
	def __init__(self):
		self.edges = {}
		self.stations = {}

	def edge(self, to, fr0m):
		if fr0m not in self.edges:
			self.edges[fr0m] = {}
		self.edges[fr0m][to] = 1

	def attach(self, prefix, station):
		self.stations[prefix] = station

	def send(self, fr0m, pkt):
		if not self.edges[fr0m]:
			print("radio: nobody listens to %s", fr0m)
			return
		for dest in self.edges[fr0m].keys():
			print("radio %s: broadcasting to %s" % (fr0m, dest))
			rssi = -50 - random.random() * 50
			async def asend():
				await asyncio.sleep(0.1 + random.random())
				self.stations[dest].radio_recv(rssi, pkt)
			loop.create_task(asend())

class Station:
	def __init__(self, prefix, radio):
		self.prefix = prefix.upper()
		self.recv_pkts = []
		self.radio = radio
		radio.attach(prefix, self)

	def send(self, to, data):
		pkt = Packet(to, "", self.prefix, data)
		self._forward(None, pkt)

	def recv(self, pkt):
		print("station %s: recv from %s msg %s" % (self.prefix, pkt.fr0m, pkt.data))

	def radio_recv(self, rssi, pkt):
		# Sanity check
		if not pkt.to or not pkt.fr0m:
			print("station %s: bad pkt %s" % (pkt.data))
			return

		# Duplicate detection
		if pkt.data in self.recv_pkts:
			print("station %s: recv dup <- %s: %s" % (self.name, pkt.fr0m, pkt.data))
			return
		self.recv_pkts.append(pkt.data)

		self._forward(rssi, pkt)

	def _forward(self, radio_rssi, pkt):
		if pkt.to == self.prefix or pkt.to == "QL" or pkt.to == "Q":
			# To myself
			self.recv(pkt)
			return

		if pkt.to == "QB" or pkt.to == "QF":
			# Broadcast pseudo-station, receive and also repeat
			self.recv(pkt)

		if pkt.fr0m != self.prefix:
			# When repeating, check TTL
			pkt.hopped += 1
			if pkt.hopped >= pkt.maxhops:
				print("station %s: drop %s <- %s: %s" % \
					(self.prefix, pkt.to, pkt.fr0m, pkt.data))
				return

		self.radio.send(self.prefix, pkt)


class Beacon:
	def __init__(self, station):
		async def sweep():
			await asyncio.sleep(random.random() * 1)
			while True:
				station.send("QB", "sweep")
				await asyncio.sleep(30 + random.random() * 60)
		loop.create_task(sweep())

r = Radio()
r.edge("B", "A") # B <- A
r.edge("A", "B")
a = Station("A", r)
b = Station("B", r)
a_beacon = Beacon(a)
b_beacon = Beacon(b)

loop.run_forever()
loop.close()
