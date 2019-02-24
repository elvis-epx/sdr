#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

class Packet:
	last_ident = 1000
	last_tag = 1

	def __init__(self, to, via, fr0m, ttl, msg, ident=None):
		self.frozen = False

		self.to = to.upper()
		self.via = via.upper()
		self.fr0m = fr0m.upper()
		self.ttl = ttl
		self.msg = msg

		# tag: ID for debugging purposes
		Packet.last_tag += 1
		self.tag = Packet.last_tag

		# ident: an ID for human consumption
		# Derived packets have similar (but different) idents
		if not ident:
			Packet.last_ident += 1
			self.ident = "%d" % Packet.last_ident
		else:
			self.ident = ident + "'"

		self.frozen = True

	def encode(self):
		return self.to + "<" + self.via + "<" + self.fr0m + " " + \
			("%d" % self.ttl) + " " + self.msg

	def decode(s):
		raise Exception("TODO")

	def __len__(self):
		return len(self.encode())

	def decrement_ttl(self):
		return Packet(self.to, self.via, self.fr0m, self.ttl - 1, self.msg, self.ident)

	def update_via(self, via):
		return Packet(self.to, via, self.fr0m, self.ttl, self.msg, self.ident)

	def replace_msg(self, msg):
		return Packet(self.to, self.via, self.fr0m, self.ttl, msg, self.ident)

	def __eq__(self, other):
		raise Exception("Packets cannot be compared")

	def __ne__(self, other):
		raise Exception("Packets cannot be compared")

	# Pseudo encoding for packet equality test
	def meaning(self):
		return self.to + "<" + self.fr0m + " " + self.msg

	# "Equal" in terms of content
	def equal(self, other):
		return self.meaning() == other.meaning()

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
