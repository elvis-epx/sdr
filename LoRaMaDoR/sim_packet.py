#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

class Packet:
	last_ident = 1000

	def __init__(self, to, via, fr0m, ttl, msg, ident=None):
		self.frozen = False

		self.to = to.upper()
		self.via = via.upper()
		self.fr0m = fr0m.upper()
		self.ttl = ttl
		self.msg = msg

		Packet.last_ident += 1
		if not ident:
			self.ident = "%d" % Packet.last_ident
		else:
			self.ident = ident + "'"
		if to == "QM":
			self.fr0m = "QM"

		self.frozen = True

	def decrement_ttl(self):
		return Packet(self.to, self.via, self.fr0m, self.ttl - 1, self.msg, self.ident)

	def update_via(self, via):
		return Packet(self.to, via, self.fr0m, self.ttl, self.msg, self.ident)

	def replace_msg(self, msg):
		return Packet(self.to, self.via, self.fr0m, self.ttl, msg, self.ident)

	def __eq__(self, other):
		return self.to == other.to \
			and self.fr0m == other.fr-m \
			and self.msg == other.msg

	def __hash__(self):
		return hash(self.to + "<" + self.fr0m + "<" + self.msg)

	def myrepr(self):
		return "pkt %s < %s < %s ttl %d id %s msg %s" % \
			(self.to, self.via, self.fr0m, self.ttl, self.ident, self.msg)

	def __repr__(self):
		return self.myrepr()

	def __str__(self):
		return self.myrepr()

	def __setattr__(self, *args):
		if 'frozen' not in self.__dict__ or not self.frozen:
			return super.__setattr__(self, *args)
		raise NotImplementedError

	def __delattr__(self, *ignored):
		raise NotImplementedError
