#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

class Packet:
	last_id = 1000
	last_tag = 2000

	def __init__(self, to, fr0m, params, msg, base_pkt=None, ):
		self.frozen = False
		self.id = Packet.last_id = Packet.last_id + 1
		self.to = to.upper()
		self.fr0m = fr0m.upper()
		self.params = params
		self.encoded_params = Packet.encode_params(self.id, self.params)
		self.msg = msg

		if not base_pkt:
			# tag: ID for human logging
			Packet.last_tag += 1
			self.tag = "%d" % Packet.last_ident
		else:
			# Derived packet
			self.tag = base_pkt.tag + "+"

		self.encoded = self.to + "<" + self.fr0m + ":" + self.encoded_params + \
			" " + self.msg

		self.frozen = True

	@staticmethod
	def encode_params(pid, params):
		s = "%d" % pid
		for k, v in params.items():
			if v is None:
				s += ",%s" % k.upper()
			else:
				s += ",%s" % (k.upper(), str(v))
		return s

	@staticmethod
	def decode(s):
		return Packet(to, fr0m, params, msg)

	def encode(self):
		return self.encoded

	def __len__(self):
		return len(self.encode())

	def replace_msg(self, msg):
		return Packet(self.to, self.fr0m, self.sparams, self.eparams, msg, self)

	def __eq__(self, other):
		raise Exception("Packets cannot be compared")

	def __ne__(self, other):
		raise Exception("Packets cannot be compared")

	# "Equal" in terms of content
	def equal(self, other):
		return self.encoded == other.encoded

	def myrepr(self):
		if self.sparams or self.eparams:
			return "pkt %s < %s id %s params %s msg %s" % \
				(self.to, self.fr0m, self.ttl, self.ident, \
				self.encoded_params, self.msg)
		return "pkt %s < %s id %s msg %s" % \
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
