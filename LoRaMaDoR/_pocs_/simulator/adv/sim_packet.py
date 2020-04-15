#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

class Packet:
	last_ident = 1000
	last_tag = 1

	def __init__(self, to, via, fr0m, ttl, msg, base_pkt=None):
		self.frozen = False

		self.to = to.upper()
		self.via = via.upper()
		self.fr0m = fr0m.upper()
		self.ttl = ttl
		self.msg = msg

		if not base_pkt:
			# New packet
			# ident: ID for human logging
			Packet.last_ident += 1
			self.ident = "%d" % Packet.last_ident
			# tag: ID for delivery debugging
			Packet.last_tag += 1
			self.tag = Packet.last_tag
		else:
			# Derived packet
			self.ident = base_pkt.ident + "'"
			self.tag = base_pkt.tag

		self.frozen = True

	def encode(self):
		return self.to + "<" + self.via + "<" + self.fr0m + " " + \
			("%d" % self.ttl) + " " + self.msg

	def decode(s):
		raise Exception("TODO")

	def __len__(self):
		return len(self.encode())

	def decrement_ttl(self):
		return Packet(self.to, self.via, self.fr0m, self.ttl - 1, self.msg, self)

	def update_via(self, via):
		return Packet(self.to, via, self.fr0m, self.ttl, self.msg, self)

	def replace_msg(self, msg):
		return Packet(self.to, self.via, self.fr0m, self.ttl, msg, self)

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
		if self.via:
			return "pkt %s < %s < %s ttl %d id %s msg %s" % \
				(self.to, self.via, self.fr0m, self.ttl, self.ident, self.msg)
		return "pkt %s << %s ttl %d id %s msg %s" % \
			(self.to, self.fr0m, self.ttl, self.ident, self.msg)

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
