#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys

L2_VERBOSITY=100
L3_VERBOSITY=50
ROUTER_VERBOSITY=80

MAX_TTL = 5

loop = asyncio.get_event_loop()

class Packet:
	last_ident = 1000

	def __init__(self, to, via, fr0m, msg):
		self.to = to.upper()
		self.via = via.upper()
		self.fr0m = fr0m.upper()

		self.ttl = MAX_TTL
		if to == "QB":
			self.ttl = 1

		Packet.last_ident += 1
		self.ident = "%d" % Packet.last_ident
		if to == "QM":
			self.fr0m = "QM"
			self.msg = msg
		else:
			self.msg = self.ident + " " + msg

	def dup(self):
		p = Packet(self.to, self.via, self.fr0m, self.msg)
		Packet.last_ident -= 1
		p.ident = self.ident + "'"
		return p

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

	def dbledge(self, to, fr0m, rssi1, rssi2=None):
		if rssi2 is None:
			rssi2 = rssi1
		self.edge(to, fr0m, rssi1)
		self.edge(fr0m, to, rssi2)

	def attach(self, callsign, station):
		self.stations[callsign] = station

	def send(self, fr0m, pkt):
		Radio.pkts_transmitted += 1

		if fr0m not in self.edges or not self.edges[fr0m]:
			print("radio %s: nobody listens to me", fr0m)
			return

		for dest, rssi in self.edges[fr0m].items():
			if rssi <= -99.9:
				if L2_VERBOSITY > 80:
					print("radio %s: not bcasting to %s, rssi too low" % \
						(fr0m, dest))
				continue
			else:
				if L2_VERBOSITY > 70:
					print("radio %s: bcasting to %s msg %s ident %s" % \
						(fr0m, dest, pkt.msg, pkt.ident))

			async def asend(d, r, p):
				await asyncio.sleep(0.1 + random.random())
				self.stations[d].radio_recv(r, p)

			loop.create_task(asend(dest, rssi, pkt.dup()))


class Router:
	def __init__(self, callsign, helper):
		self.routes = []
		self.callsign = callsign
		self.edges = {}
		self.sent_edges = {}
		self.helper = helper

	def learn(self, ident, ttl, path, last_hop_rssi):
		# Extract graph edges from breadcrumb path
		if not path:
			return

		if ttl > 0:
			# path[0] is neighbor
			path = [ self.callsign ] + path

		if ROUTER_VERBOSITY > 90:
			print("%s rt: learning path %s ident %s ttl %d" \
				% (self.callsign, " < ".join(path), ident, ttl))

		for i in range(0, len(path) - 1):
			to = path[i]
			fr0m = path[i+1]
			print("#### %s %s %s" % (str(path), to, fr0m))

			if to == fr0m:
				print("#### FATAL %s <- %s" % (to, fr0m))
				sys.exit(1)

			cost = 1000
			if i == 0:
				# Cost of adjacent node = -RSSI
				cost = -last_hop_rssi

			# FIXME cost not being propagated

			if to not in self.edges:
				self.edges[to] = {}
				self.sent_edges[to] = {}

			if fr0m not in self.edges[to]:
				self.edges[to][fr0m] = cost
				self.sent_edges[to][fr0m] = False
				if ROUTER_VERBOSITY > 50:
					print("%s rt: learnt edge %s < %s" % \
						(self.callsign, to, fr0m))

			elif self.edges[to][fr0m] > cost:
				self.edges[to][fr0m] = cost
				if ROUTER_VERBOSITY > 50:
					print("%s rt: reduced cost %s < %s" % \
						(self.callsign, to, fr0m))

		if ROUTER_VERBOSITY > 50:
			learnt_edges = sum(len(v.keys()) for k, v in self.edges.items())
			total_edges = self.helper['total_edges']()
			pp = 100 * learnt_edges / total_edges
			print("%s (dbg) rt knows %.1f%% of the graph" % (self.callsign, pp))
			print("\tknows: ", self.edges)

	def prune(self, left_is_us, path):
		# Remove heading and trailing edges that we have already published
		# NOTE: assume that path was already learn()ed
		path_before = path[:]
		path = path[:]

		if ROUTER_VERBOSITY > 90:
			print("%s rt: pruning path %s" % (self.callsign, " < ".join(path)))

		if left_is_us:
			# Cannot prune at left because of guarantee that
			# path[0] == ourselves when ttl > 0
			pass
		else:
			# Prune at left
			while len(path) >= 2:
				to = path[0]
				fr0m = path[1]
				if self.sent_edges[to][fr0m]:
					# Already sent, prune
					path = path[1:]
					if ROUTER_VERBOSITY > 90:
						print("%s rt: pruned edge %s < %s" % \
							(self.callsign, to, fr0m))
				else:
					# Mark as sent and stop pruning this end
					self.sent_edges[to][fr0m] = True
					break
	
		# Prune at right
		while len(path) >= 2:
			to = path[-2]
			fr0m = path[-1]
			if self.sent_edges[to][fr0m]:
				# Already sent, prune
				path = path[:-1]
				if ROUTER_VERBOSITY > 90:
					print("%s rt: pruned edge %s < %s" % \
						(self.callsign, to, fr0m))
			else:
				# Mark as sent and stop pruning
				self.sent_edges[to][fr0m] = True
				break
		
		if len(path) < 2:
			path = []

		if ROUTER_VERBOSITY > 90:
			if len(path_before) != len(path):
				print("\tbefore pruning: %s" % " < ".join(path_before))
				print("\tafter pruning: %s" % " < ".join(path))

		return path

	def sent(self, ident, ttl, path):
		if ROUTER_VERBOSITY > 60:
			print("%s rt: sent ttl %d ident %s path %s" % \
				(self.callsign, ttl, ident, " < ".join(path)))

		for i in range(0, len(path) - 1):
			self.sent_edges[path[i]][path[i + 1]] = True


class Station:
	pending_pkts = []

	def __init__(self, callsign, radio):
		self.callsign = callsign.upper()
		self.recv_pkts = []
		self.generators = []
		self.radio = radio

		# For debugging purposes
		def total_edges():
			return sum(len(v.keys()) for k, v in self.radio.edges.items())
		helper = {"total_edges": total_edges}

		self.router = Router(self.callsign, helper)
		radio.attach(callsign, self)

	def send(self, to, msg):
		# Called when we originate a packet
		pkt = Packet(to, "", self.callsign, msg)
		if pkt.to != "QM":
			Station.pending_pkts.append(pkt.msg)
		print("%s -> %s msg %s" % (self.callsign, pkt.to, pkt.msg))
		self._forward(None, pkt, True)

	def recv(self, pkt):
		# Called when we are the recipient of a packet
		if pkt.msg in Station.pending_pkts:
			Station.pending_pkts.remove(pkt.msg)
		if pkt.to == self.callsign:
			print("%s <- %s msg %s" % 
				(self.callsign, pkt.fr0m, pkt.msg))
		else:
			print("%s (%s) <- %s msg %s" % 
				(self.callsign, pkt.to, pkt.fr0m, pkt.msg))

	def radio_recv(self, rssi, pkt):
		# Got a packet from radio, we don't know who sent it
		if L3_VERBOSITY > 80:
			print("%s: recv rssi %d" % (self.callsign, rssi))

		# Sanity check
		if not pkt.to or not pkt.fr0m:
			print("%s: bad pkt %s" % (pkt.msg))
			return

		# Level 3 handling
		self._forward(rssi, pkt, False)

	def _forward(self, radio_rssi, pkt, from_us):
		# Handle the packet in L3

		if from_us:
			# We are the origin
			if pkt.to in ("QL", "Q", self.callsign):
				# Loopback
				self.recv(pkt)
				return
			# Annotate to detect duplicates
			self.recv_pkts.append(pkt.msg)
			# Send away
			self.radio.send(self.callsign, pkt)
			return

		if pkt.to == "QM" or pkt.fr0m == "QM":
			# Mesh / route special message from remote
			self._mesh_formation(radio_rssi, pkt)
			return

		# Discard received duplicates
		if pkt.msg in self.recv_pkts:
			if L3_VERBOSITY > 80:
				print("%s: recv dup %s <- %s: %s" % 
					(self.callsign, pkt.to, pkt.fr0m, pkt.msg))
			return
		self.recv_pkts.append(pkt.msg)

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

	def _repeat(pkt):
		######## Repeater logic

		# Hop count control
		pkt.ttl -= 1
		if pkt.ttl <= 0:
			if L3_VERBOSITY > 90:
				print("%s: drop %s <- %s: %s" % \
					(self.callsign, pkt.to, pkt.fr0m, pkt.msg))
			return

		if pkt.via:
			# Active routing
			if pkt.via != self.callsign:
				# Not for us to forward
				if L3_VERBOSITY > 80:
					print("%s: not forwarding %s <- %s: %s" % \
						(self.callsign, pkt.to, pkt.fr0m, pkt.msg))
					return

			# Find next hop
			next_hop = self.get_next_hop(pkt)
			if not next_hop:
				if L3_VERBOSITY > 50:
					print("%s: could not route %s -> %s: %s" % 
						(self.callsign, pkt.fr0m, pkt.to, pkt.msg))
				return

			pkt.via = next_hop

			if L3_VERBOSITY > 50:
				print("%s: forwarding %s -> %s: %s" % 
					(self.callsign, pkt.fr0m, pkt.to, pkt.msg))

		if not pkt.via:
			# Diffusion routing, forwarding blindly
			if L3_VERBOSITY > 60:
				print("%s: forwarding %s -> %s: %s" % 
					(self.callsign, pkt.fr0m, pkt.to, pkt.msg))

		self.radio.send(self.callsign, pkt)

	def get_next_hop(self, pkt):
		# TODO implement routing logic
		return None

	def _mesh_formation(self, radio_rssi, pkt):
		# Handle mesh formation packet

		if pkt.to != "QM" or pkt.fr0m != "QM":
			if ROUTER_VERBOSITY > 40:
				print("%s: Bad QM packet addr", self.callsign)
			return

		msg = pkt.msg.upper().strip()
		if not msg:
			if ROUTER_VERBOSITY > 40:
				print("%s: Bad QM packet msg", self.callsign)
			return


		# Parse message into a path
		path = msg.split("<")
		if ROUTER_VERBOSITY > 50:
			print("%s: rt recv path %s ttl %d ident %s" % \
				(self.callsign, "<".join(path), pkt.ttl, pkt.ident))

		self.router.learn(pkt.ident, pkt.ttl, path, radio_rssi)

		# Hop count control
		pkt.ttl -= 1

		if pkt.ttl <= -MAX_TTL:
			if ROUTER_VERBOSITY > 60:
				print("\tnot forwarding - ttl")
			return

		# Only add ourselves to path if len(path) < TTL
		if pkt.ttl > 0:
			path = [ self.callsign ] + path

		# Prune parts of the route we've already broadcasted
		# but guarantee that path[0] = us when ttl > 0
		path = self.router.prune(pkt.ttl > 0, path)
		if len(path) < 2:
			if ROUTER_VERBOSITY > 90:
				print("\tnothing left after pruning")
			return

		# Forward with updated path
		pkt.msg = "<".join(path)
		self.radio.send(self.callsign, pkt)
		self.router.sent(pkt.ident, pkt.ttl, path)

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


class MeshFormation:
	def __init__(self, station):
		async def probe():
			await asyncio.sleep(1 + random.random() * 5)
			while True:
				station.send("QM", station.callsign)
				await asyncio.sleep(60 + random.random() * 60)
		loop.create_task(probe())


def radio():
	return Radio()

def aioloop():
	return loop

def run():
	async def list_pending_pkts():
		while True:
			await asyncio.sleep(120)
			print("Packets pending delivery:", Station.pending_pkts)
	loop.create_task(list_pending_pkts())

	loop.run_forever()
	loop.close()
