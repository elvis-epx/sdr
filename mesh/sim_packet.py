#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

class Packet:
	def __init__(self, to, fr0m, ident, params, msg):
		self.frozen = False
		self.ident = ident
		self.to = to.upper()
		self.fr0m = fr0m.upper()
		self.params = params
		self.encoded_params = Packet.encode_params(ident, self.params)
		self.msg = msg

		self.encoded = self.to + "<" + self.fr0m + ":" \
			+ self.encoded_params + " " + self.msg

		self.frozen = True

	@staticmethod
	def encode_params(ident, params):
		s = "%d" % ident
		for k, v in params.items():
			if v is None:
				s += ",%s" % k.upper()
			else:
				s += ",%s=%s" % (k.upper(), str(v))
		return s

	@staticmethod
	def check_callsign(s):
		s = s.upper()
		if len(s) < 2:
			return None
		if len(s) == 2 and s[0] != "Q":
			return None
		if len(s) > 2 and s[0] == "Q":
			return None
		if not s[0].isalpha():
			return None
		ssid_delim = s.find("-")
		if ssid_delim > -1:
			prefix, ssid = s[:ssid_delim], s[ssid_delim+1:]
			if len(ssid) <= 0 or len(ssid) > 2:
				return None
			for c in ssid:
				if not c.isdigit():
					return None
		else:
			prefix = s

		if len(prefix) > 7 or len(prefix) < 4:
			return None

		for c in prefix:
			if not c.isdigit() and not c.isalpha():
				return None
		return s

	@staticmethod
	def parse_symbol_param(s):
		nok = (False, None, None, None)
		eq = s.find("=")
		if eq > -1:
			# Type is key=value
			key, value = s[:eq], s[eq+1:]
			if not value:
				return nok
		else:
			# Type is naked key
			key, value = s, None

		if not key:
			return nok

		for c in key:
			if not c.isalpha() and not c.isdigit():
				return nok

		if value is not None:
			for c in value:
				if c in ("=", " ", ",", ":", "<"):
					return nok

		return True, None, key, value

	@staticmethod
	def parse_ident_param(s):
		try:
			ident = int(s)
		except ValueError:
			return False, None, None, None
		if len("%d" % ident) != len(s):
			return False, None, None, None
		return True, ident, None, None

	@staticmethod
	def parse_param(s):
		if len(s) <= 0:
			return False, None, None, None
		if s[0].isdigit():
			# Probably the packet id
			return Packet.parse_ident_param(s)
		elif s[0].isalpha():
			# Optional parameter (naked_key or key=value)
			return Packet.parse_symbol_param(s)
		else:
			return False, None, None, None

	@staticmethod
	def parse_params(s):
		ident = None
		params = {}
		
		ss = s.split(",")
		for sp in ss:
			ok, number, param, value = Packet.parse_param(sp)
			if not ok:
				return None, None
			if number is not None:
				ident = number
			else:
				params[param.upper()] = value

		return ident, params

	@staticmethod
	def decode_preamble(s):
		nok = (None, None, None, None, None)
		d1 = s.find("<")
		d2 = s.find(":")
		if d1 == -1 or d2 == -1 or d1 >= d2:
			return nok
		to_s = s[:d1]
		from_s = s[d1+1:d2]
		params_s = s[d2+1:]
		to = Packet.check_callsign(to_s)
		fr0m = Packet.check_callsign(from_s)
		ident, params = Packet.parse_params(params_s)
		ok = to and fr0m and (ident is not None)
		return ok, to, fr0m, ident, params

	@staticmethod
	def decode(s):
		if len(s) > 250:
			return None
		msgd = s.find(" ")
		if msgd >= 0:
			preamble, msg = s[:msgd], s[(msgd + 1):]
		else:
			preamble = s
			msg = ""
		ok, to, fr0m, ident, params = Packet.decode_preamble(preamble)
		if not ok:
			return None
		
		return Packet(to, fr0m, ident, params, msg)

	def encode(self):
		return self.encoded

	def __len__(self):
		return len(self.encode())

	def __eq__(self, other):
		raise Exception("Packets cannot be compared")

	def __ne__(self, other):
		raise Exception("Packets cannot be compared")

	def duplicate(self, other):
		return self.to == other.to and self.fr0m == other.fr0m \
			and self.ident == other.ident

	def myrepr(self):
		return "pkt %s < %s : %s msg %s" % \
			(self.to, self.fr0m, self.encoded_params, self.msg)

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


if __name__ == "__main__":
	p = Packet("aaAA", "BBbB", 123, {"x": None, "y": 456}, "bla")
	sp = p.encode()
	assert (sp == "AAAA<BBBB:123,X,Y=456 bla")
	q = Packet.decode(sp)
	assert (p.duplicate(q) and q.duplicate(p))
	assert (q.to == "AAAA")
	assert (q.fr0m == "BBBB")
	assert (q.ident == 123)
	assert ("X" in q.params)
	assert ("Y" in q.params)
	assert (q.params["Y"] == "456")
	assert (q.params["X"] is None)

	print("Autotest ok")
