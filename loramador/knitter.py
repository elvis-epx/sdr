#!/usr/bin/env/python3

def Packet:
	def __init__(to, frm, data):
		self.to = to
		self.frm = frm
		self.data = data
		self.ttl = 5

class Route:
	def __init__(to, nxt, cost, timestamp):
		self.to = to
		self.nxt = nxt
		self.cost = cost
		self.timestamp = ts

class L2:
	

class L3:
	def __init__(self, name, l2):
		self.name = name
		self.routes = []
		self.l2 = l2

	def send(self, to, data):
		pkt = Packet(to, self.name, data)
		self.forward(pkt)

	def recv(self, pkt):
		print "recv from %s: %s" % (pkt.frm, pkt.data)

	def l2_recv(self, to, frm, rssi, pkt):
		self.forward(frm, rssi, pkt)

	def add_route(l2_from, cost):
		new_route = Route()

		old_route = -1
		for i, route in enumerate(self.routes):
			if route.to == new_route.to and route.nxt == new_route.nxt:
				if route.timestamp >= new_route:
					print ("%s: new route to %s is old" % (self.name, new_route.to))
					return
				old_route = i

		if old_route >= 0:
			# print ("%s: replacing route to %s" % (self.name, new_route.to))
			self.routes[old_route] = new_route
		else:
			print ("%s: adding route to %s" % (self.name, new_route.to))
			self.routes.append(new_route)

	def next_hop(self, to):
		cost = 9999999999
		hops = 9999999999
		best = None
		for route in self.routes:
			if route.to != to:
				pass
			elif route.hops > 1 and hops > 1:
				if route.hops < hops:
					best = route.nxt
					cost = route.cost
			elif route.hops == 1 and hops > 1:
				best = route.nxt
				cost = route.cost
			else:
				if route.cost < cost:
					best = route.next
					cost = route.cost
		return best

	def forward(self, l2_frm, l2_rssi, pkt):
		self.add_route(l2_frm, l2_rssi)

		if pkt.to == self.name:
			self.recv(pkt)
			return

		if pkt.frm != self.name:
			pkt.ttl -= 1
			if pkt.ttl <= 0:
				print "%s: packet %s<-%s discarded" % (self.name, pkt.to, pkt.frm)
				return

		nxt = self.next_hop(pkt.to)
		if not nxt:
			if pkt.frm != self.name:
				print "%s: no route to %s" % (self.name, pkt.to)
			else:
				print "%s in behalf of %s: no route to %s" % (self.name, pkt.frm, pkt.to)
			return

		self.l2.send(nxt, self.name, pkt)

