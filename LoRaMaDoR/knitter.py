#!/usr/bin/env python3

import random, math, asyncio

STATION_COUNT=10
VERBOSITY=100

loop = asyncio.get_event_loop()

class Packet:
	last_ident = 0

	def __init__(self, to, via, fr0m, data):
		self.to = to.upper()
		self.via = via.upper()
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

	def edge(self, to, fr0m, rssi):
		if fr0m not in self.edges:
			self.edges[fr0m] = {}
		self.edges[fr0m][to] = rssi

	def attach(self, callsign, station):
		self.stations[callsign] = station

	def send(self, fr0m, pkt):
		Radio.pkts_transmitted += 1

		if fr0m not in self.edges or not self.edges[fr0m]:
			print("radio %s: nobody listens to me", fr0m)
			return

		for dest, rssi in self.edges[fr0m].items():
			if rssi <= -99.9:
				if VERBOSITY > 80:
					print("radio %s: not bcasting to %s, rssi too low" % (fr0m, dest))
				continue
			else:
				if VERBOSITY > 70:
					print("radio %s: bcasting to %s" % (fr0m, dest))

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
		# Called when we originate a packet
		pkt = Packet(to, "", self.callsign, data)
		Station.pending_pkts.append(pkt.data)
		print("%s -> %s msg %s" % (self.callsign, pkt.to, pkt.data))
		self._forward(None, pkt)

	def recv(self, pkt):
		# Called when we are the recipient of a packet
		if pkt.data in Station.pending_pkts:
			Station.pending_pkts.remove(pkt.data)
		if pkt.to == self.callsign:
			print("%s <- %s msg %s" % 
				(self.callsign, pkt.fr0m, pkt.data))
		else:
			print("%s (%s) <- %s msg %s" % 
				(self.callsign, pkt.to, pkt.fr0m, pkt.data))

	def radio_recv(self, rssi, pkt):
		# Got a packet from radio, we don't know who sent it
		if VERBOSITY > 80:
			print("%s: recv rssi %d" % (self.callsign, rssi))

		# Sanity check
		if not pkt.to or not pkt.fr0m:
			print("%s: bad pkt %s" % (pkt.data))
			return

		# Level 3 handling
		self._forward(rssi, pkt)

	def _forward(self, radio_rssi, pkt):
		# Handle the packet in L3

		# Discard duplicates
		if pkt.data in self.recv_pkts:
			if VERBOSITY > 80:
				print("%s: recv dup %s <- %s: %s" % 
					(self.callsign, pkt.to, pkt.fr0m, pkt.data))
			return
		self.recv_pkts.append(pkt.data)

		if pkt.to == self.callsign or pkt.to in ("QL", "Q"):
			# We are the final destination
			self.recv(pkt)
			return

		if pkt.to in ("QB", "QF"):
			# We are one of the recipients
			self.recv(pkt)

		if pkt.fr0m == self.callsign:
			# We are the originators
			self.radio.send(self.callsign, pkt)
			return

		######## Repeater logic

		# Hop count control
		pkt.hopped += 1
		if pkt.hopped >= pkt.maxhops:
			if VERBOSITY > 90:
				print("%s: drop %s <- %s: %s" % \
					(self.callsign, pkt.to, pkt.fr0m, pkt.data))
			return

		if pkt.via:
			# Active routing
			if pkt.via != self.callsign:
				# Not for us to forward
				if VERBOSITY > 80:
					print("%s: not forwarding %s <- %s: %s" % \
						(self.callsign, pkt.to, pkt.fr0m, pkt.data))
					return

			# Find next hop
			next_hop = self.get_next_hop(pkt)
			if not next_hop:
				if VERBOSITY > 50:
					print("%s: could not route %s -> %s: %s" % 
						(self.callsign, pkt.fr0m, pkt.to, pkt.data))
				return

			pkt.via = next_hop

			if VERBOSITY > 50:
				print("%s: forwarding %s -> %s: %s" % 
					(self.callsign, pkt.fr0m, pkt.to, pkt.data))

		if not pkt.via:
			# Diffusion routing, forwarding blindly
			if VERBOSITY > 60:
				print("%s: forwarding %s -> %s: %s" % 
					(self.callsign, pkt.fr0m, pkt.to, pkt.data))

		self.radio.send(self.callsign, pkt)

	def get_next_hop(self, pkt):
		# TODO implement routing logic
		return None

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
stations = {}

# create stations
for i in range(0, STATION_COUNT):
	callsign = chr(ord('A') + i)
	stations[callsign] = Station(callsign, r)

# create model mesh
r.edge("A", "B", -50)  # "A" <- "B", rssi -50
r.edge("A", "C", -70)

r.edge("C", "A", -60)
r.edge("C", "B", -75)
r.edge("C", "E", -80)
r.edge("C", "F", -60)

r.edge("B", "A", -55)
r.edge("B", "C", -75)
r.edge("B", "D", -51)
r.edge("B", "E", -51)

r.edge("D", "B", -45)
r.edge("D", "E", -65)
r.edge("D", "G", -85)

r.edge("E", "B", -70)
r.edge("E", "C", -60)
r.edge("E", "D", -90)
r.edge("E", "F", -120) # out
r.edge("E", "G", -65)
r.edge("E", "H", -62)

r.edge("F", "C", -120) # out
r.edge("F", "E", -120) # out
r.edge("F", "H", -80) 

r.edge("G", "D", -61)
r.edge("G", "E", -62)
r.edge("G", "H", -63)
r.edge("G", "I", -119) # out

r.edge("H", "F", -120) # out
r.edge("H", "E", -66) 
r.edge("H", "G", -60) 
r.edge("H", "I", -47) 

r.edge("I", "G", -40) 
r.edge("I", "H", -70) 
r.edge("I", "J", -65)

r.edge("J", "I", -60) 

# add talkers
for callsign, station in stations.items():
	station.add(Beacon).add(RagChewer)

async def list_pending_pkts():
	while True:
		await asyncio.sleep(10)
		print("Packets pending delivery:", Station.pending_pkts)
loop.create_task(list_pending_pkts())

loop.run_forever()
loop.close()
