#!/usr/bin/env python3

import random, math, asyncio

VERBOSITY=61

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
	pkts_transmitted = 0

	def __init__(self):
		self.edges = {}
		self.stations = {}
		async def transmitted():
			while True:
				await asyncio.sleep(60)
				print("##### radio: sent %d pkts" % Radio.pkts_transmitted)
		loop.create_task(transmitted())

	def edge(self, to, fr0m):
		if fr0m not in self.edges:
			self.edges[fr0m] = {}
		self.edges[fr0m][to] = 1

	def attach(self, callsign, station):
		self.stations[callsign] = station

	def send(self, fr0m, pkt):
		Radio.pkts_transmitted += 1

		if fr0m not in self.edges or not self.edges[fr0m]:
			print("radio %s: nobody listens to me", fr0m)
			return

		for dest in self.edges[fr0m].keys():
			if VERBOSITY > 70:
				print("radio %s: broadcasting to %s" % (fr0m, dest))
			rssi = -50 - random.random() * 50
			async def asend(d, r, p):
				await asyncio.sleep(0.1 + random.random())
				self.stations[d].radio_recv(r, p)
			loop.create_task(asend(dest, rssi, pkt))


class Station:
	pending_pkts = []

	def __init__(self, callsign, radio):
		self.callsign = callsign.upper()
		self.recv_pkts = []
		self.generators = []
		self.radio = radio
		radio.attach(callsign, self)

	def send(self, to, data):
		pkt = Packet(to, "", self.callsign, data)
		Station.pending_pkts.append(pkt.data)
		print("%s -> %s msg %s" % (self.callsign, pkt.to, pkt.data))
		self._forward(None, pkt)

	def recv(self, pkt):
		if pkt.data in Station.pending_pkts:
			Station.pending_pkts.remove(pkt.data)
		if pkt.to == self.callsign:
			print("%s <- %s msg %s" % 
				(self.callsign, pkt.fr0m, pkt.data))
		else:
			print("%s (%s) <- %s msg %s" % 
				(self.callsign, pkt.to, pkt.fr0m, pkt.data))

	def radio_recv(self, rssi, pkt):
		# Sanity check
		if not pkt.to or not pkt.fr0m:
			print("%s: bad pkt %s" % (pkt.data))
			return

		self._forward(rssi, pkt)

	def _forward(self, radio_rssi, pkt):
		# Duplicate detection
		if pkt.data in self.recv_pkts:
			if VERBOSITY > 80:
				print("%s: recv dup %s <- %s: %s" % 
					(self.callsign, pkt.to, pkt.fr0m, pkt.data))
			return
		self.recv_pkts.append(pkt.data)

		if pkt.to == self.callsign or pkt.to in ("QL", "Q"):
			# I am the recipient
			self.recv(pkt)
			return

		if pkt.fr0m != self.callsign:
			# I am repeater
			if pkt.to in ("QB", "QF"):
				# Broadcast pseudo-destination, I am a recipient too
				self.recv(pkt)

			# Check TTL
			pkt.hopped += 1
			if pkt.hopped >= pkt.maxhops:
				if VERBOSITY > 90:
					print("%s: drop %s <- %s: %s" % \
						(self.callsign, pkt.to, pkt.fr0m, pkt.data))
				return

			if VERBOSITY > 60:
				print("%s: forward %s -> %s: %s" % 
					(self.callsign, pkt.fr0m, pkt.to, pkt.data))

		self.radio.send(self.callsign, pkt)

	def add(self, klass):
		self.generators.append(klass(self))
		return self


class Beacon:
	def __init__(self, station):
		async def beacon():
			await asyncio.sleep(random.random() * 1)
			while True:
				station.send("QB", "beacon")
				await asyncio.sleep(30 + random.random() * 60)
		loop.create_task(beacon())


class RagChewer:
	def __init__(self, station):
		async def talk():
			while True:
				await asyncio.sleep(15 + random.random() * 30)
				to_options = list(station.radio.stations.keys())
				to_options.remove(station.callsign)
				to = random.choice(to_options)
				station.send(to, "bla")
		loop.create_task(talk())


r = Radio()
# Mesh map
r.edge("B", "A") # B <- A i.e. A can send to B
r.edge("A", "B")
r.edge("A", "C")
r.edge("C", "A")
r.edge("A", "D")
r.edge("D", "A")
r.edge("B", "C")
r.edge("C", "B")
r.edge("B", "D")
r.edge("D", "B")
r.edge("C", "D")
r.edge("D", "C")

a = Station("A", r).add(Beacon).add(RagChewer)
b = Station("B", r).add(Beacon).add(RagChewer)
c = Station("C", r).add(Beacon).add(RagChewer)
d = Station("D", r).add(Beacon).add(RagChewer)

async def list_pending_pkts():
	while True:
		await asyncio.sleep(10)
		print("Packets pending delivery:", Station.pending_pkts)
loop.create_task(list_pending_pkts())

loop.run_forever()
loop.close()
