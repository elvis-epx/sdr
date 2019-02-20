#!/usr/bin/env/python3

def Packet:
	def __init__(to, frm, data):
		self.to = to.upper()
		self.frm = frm.upper()
		self.data = data
		self.ttl = 5

class Hop:
	def __init__(to, frm, cost, timestamp):
		self.to = to.upper()
		self.frm = frm.upper()
		self.cost = cost
		self.timestamp = ts

class L2:
	def __init__(self):
		self.vertexes = {}
		self.l3 = {}

	def attach(self, name, l3obj):
		self.l3[name] = l3obj

	def send(self, to, frm, pkt):
		if not self.vertexes[frm]:
			print("L2: can't send pkt from %s to anywhere", frm)
			return
		for dest in self.vertexes[frm]:
			self.vertexes[frm][dest].l2_recv(to, frm, -50-random.random()*50, pkt)

class L3:
	def __init__(self, name, l2):
		self.name = name.upper()
		self.hops = []
		self.l2 = l2
		l2.attach(name, self)

	def send(self, to, data):
		pkt = Packet(to, self.name, data)
		self.forward(pkt)

	def recv(self, pkt):
		print "recv from %s: %s" % (pkt.frm, pkt.data)

	def l2_recv(self, to, frm, rssi, pkt):
		to = to.upper()
		frm = frm.upper()
		self.forward(frm, -rssi, pkt)

	def add_hop(l2_to, l2_from, cost):
		# Add/update hop from neighbor
		new_hop = Hop(l2_from, l2_from, 1, cost, time.time())

		old_hop = -1
		for i, hop in enumerate(self.hops):
			if hop.to == new_hop.to and hop.frm == new_hop.frm:
				if hop.timestamp >= new_hop:
					print ("%s: new hop %s<-%s is old" % (self.name, new_hop.to, new_hop.frm))
					return
				old_hop = i

		if old_hop >= 0:
			# print ("%s: replacing hop to %s" % (self.name, new_hop.to))
			self.hops[old_hop] = new_hop
		else:
			print ("%s: adding hop to %s" % (self.name, new_hop.to))
			self.hops.append(new_hop)

	def find_next_hop(self, to):
		return self._find_next_hop(to, [], 10)

	def _find_next_hop(self, to, path, maxhops):
		best = None
		hopcount = 999999999
		cost = 999999999

		if maxhops <= 0:
			# maximum diameter reached
			return None, None, None

		if self.name in path:
			# loop detected
			return None, None, None

		path = path[:] + [to]

		for hop in self.hops:
			if hop.to != to:
				continue

			if hop.frm == self.name:
				# we are neighbors to the destination
				best = hop
				hopcount = 0
				cost = hop.cost
				break

			# found a station that is neighbor of the destination
			# Find path to that station (hop.frm) recursively 
			# TODO extremely inefficient way to find route

			# Don't go further the best path we've already found
			cmaxhops = min(maxhops - 1, hopcount)
			candidate, chopcount, ccost = self._find_next_hop(hop.frm, path, cmaxhops)
			if not candidate:
				continue

			if chopcount < hopcount or (chopcount == hopcount and ccost < cost):
				best = hop
				hopcount = chopcount
				cost = ccost

		return best, hopcount + 1, cost + 1000

	def forward(self, l2_frm, l2_rssi, pkt):
		if l2_from[0] != "Q":
			self.add_hop(self.name, l2_frm, -l2_rssi)

		if pkt.to == self.name:
			self.recv(pkt)
			return

		if pkt.frm != self.name:
			pkt.ttl -= 1
			if pkt.ttl <= 0:
				print "%s: packet %s<-%s discarded" % (self.name, pkt.to, pkt.frm)
				return

		nxt, hops, cost = self.find_next_hop(pkt.to)
		if not nxt:
			if pkt.frm != self.name:
				print "%s: no route to %s" % (self.name, pkt.to)
			else:
				print "%s in behalf of %s: no route to %s" % (self.name, pkt.frm, pkt.to)
			return

		self.l2.send(nxt, self.name, pkt)
