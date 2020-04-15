#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

class Packet:
	def __init__(self, to, fr0m, ident, params, msg):
		self.frozen = False
		self.ident = ident
		self.to = Packet.check_callsign(to)
		self.fr0m = Packet.check_callsign(fr0m)
		if not self.to or not self.fr0m:
			raise Exception("Invalid callsign")
		self.params = params.copy()
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
		if len(s) == 2:
			if s[0] != "Q":
				return None
			elif not s[1].isalpha():
				return None
			return s
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
			if ("%d" % int(ssid)) != ssid:
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
		eq = s.find("=")
		if eq > -1:
			# Type is key=value, value may be empty
			key, value = s[:eq], s[eq+1:]
		else:
			# Type is naked key
			key, value = s, None

		if not key:
			return None

		for c in key:
			if not c.isalpha() and not c.isdigit():
				return None

		if value is not None:
			for c in value:
				if c in ("=", " ", ",", ":", "<"):
					return None

		return None, key, value

	@staticmethod
	def parse_ident_param(s):
		try:
			ident = int(s)
		except ValueError:
			return None
		if ("%d" % ident) != s:
			return None
		return ident, None, None

	@staticmethod
	def parse_param(s):
		if len(s) <= 0:
			return None
		elif s[0].isdigit():
			# Probably the packet id
			return Packet.parse_ident_param(s)
		elif s[0].isalpha():
			# Optional parameter (naked_key or key=value)
			return Packet.parse_symbol_param(s)
		return None

	@staticmethod
	def parse_params(s):
		ident = None
		params = {}
		
		ss = s.split(",")
		for sp in ss:
			parsed_param = Packet.parse_param(sp)
			if not parsed_param:
				return None, None
			number, param, value = parsed_param
			if number is not None:
				ident = number
			else:
				params[param.upper()] = value

		return ident, params

	@staticmethod
	def decode_preamble(s):
		d1 = s.find("<")
		d2 = s.find(":")
		if d1 == -1 or d2 == -1 or d1 >= d2:
			return None
		to_s = s[:d1]
		from_s = s[d1+1:d2]
		params_s = s[d2+1:]
		to = Packet.check_callsign(to_s)
		fr0m = Packet.check_callsign(from_s)
		ident, params = Packet.parse_params(params_s)
		ok = to and fr0m and (ident is not None)
		if not ok:
			return None
		return to, fr0m, ident, params

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
		preamble = Packet.decode_preamble(preamble)
		if not preamble:
			return None
		to, fr0m, ident, params = preamble
		
		return Packet(to, fr0m, ident, params, msg)

	def change_msg(self, msg):
		return Packet(self.to, self.fr0m, self.ident, self.params, msg)

	def append_param(self, k, v):
		params = self.params.copy()
		params[k] = v
		return Packet(self.to, self.fr0m, self.ident, params, self.msg)

	def encode(self):
		return self.encoded

	def __len__(self):
		return len(self.encode())

	def __eq__(self, other):
		raise Exception("Packets cannot be compared")

	def __ne__(self, other):
		raise Exception("Packets cannot be compared")

	def signature(self):
		return self.fr0m + ":" + "%d" % self.ident

	def duplicate(self, other):
		return self.signature() == other.signature()

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
	p = Packet("aaAA", "BBbB", 123, {"x": None, "y": 456}, "bla ble")
	sp = p.encode()
	assert (sp == "AAAA<BBBB:123,X,Y=456 bla ble")
	q = Packet.decode(sp)
	assert (p.duplicate(q) and q.duplicate(p))
	assert (q.to == "AAAA")
	assert (q.fr0m == "BBBB")
	assert (q.ident == 123)
	assert ("X" in q.params)
	assert ("Y" in q.params)
	assert (q.params["Y"] == "456")
	assert (q.params["X"] is None)

	assert (Packet.check_callsign("Q") is None)
	assert (Packet.check_callsign("QB") is not None)
	assert (Packet.check_callsign("QC") is not None)
	assert (Packet.check_callsign("Q1") is None)
	assert (Packet.check_callsign("Q-") is None)
	assert (Packet.check_callsign("qcc") is None)
	assert (Packet.check_callsign("xc") is None)
	assert (Packet.check_callsign("1cccc") is None)
	assert (Packet.check_callsign("aaaaa-1a") is None)
	assert (Packet.check_callsign("aaaaa-01") is None)
	assert (Packet.check_callsign("a#jskd") is None)
	assert (Packet.check_callsign("-1") is None)
	assert (Packet.check_callsign("aaa-1") is None)
	assert (Packet.check_callsign("aaaa-1-2") is None)
	assert (Packet.check_callsign("aaaa-123") is None)

	p = Packet.decode("AAAA<BBBB:133")
	assert (p is not None)
	assert (p.msg == "")

	p = Packet.decode("AAAA-12<BBBB:133 ee")
	assert (p is not None)
	assert (p.msg == "ee")
	assert (p.to == "AAAA-12")
	
	assert (Packet.decode("AAAA:BBBB<133") is None)
	assert (Packet.decode("AAAA<BBBB:133,aaa,bbb=ccc,ddd=eee,fff bla") is not None)
	assert (Packet.decode("AAAA<BBBB:133,aaa,,ddd=eee,fff bla") is None)
	assert (Packet.decode("AAAA<BBBB:01 bla") is None)
	assert (Packet.decode("AAAA<BBBB:aa bla") is None)

	assert (len(Packet.parse_params("123")) == 2)
	p = Packet.parse_params("1234")
	assert (p[0] == 1234)
	p = Packet.parse_params("1234,abc")
	assert (p[0] == 1234)
	assert (("ABC" in p[1]) and (p[1]["ABC"] is None))

	p = Packet.parse_params("1234,abc,def=ghi")
	assert (p[0] == 1234)
	assert ("ABC" in p[1] and p[1]["ABC"] is None)
	assert ("DEF" in p[1] and p[1]["DEF"] == "ghi")
	assert (len(p[1].keys()) == 2)

	p = Packet.parse_params("def=ghi,1234")
	assert (p[0] == 1234)
	assert(len(p[1].keys()) == 1)
	assert ("DEF" in p[1] and p[1]["DEF"] == "ghi")

	assert (Packet.parse_params("123a")[0] is None)
	assert (Packet.parse_params("0123")[0] is None)
	assert (Packet.parse_params("abc")[0] is None)
	assert (Packet.parse_params("abc=def")[0] is None)
	assert (Packet.parse_params("123,0bc=def")[0] is None)
	assert (Packet.parse_params("123,0bc")[0] is None)
	assert (Packet.parse_params("123,,bc")[0] is None)
	assert (Packet.parse_params("1,abc=def")[0] is not None)
	assert (Packet.parse_params("1,2,abc=def")[0] == 2)
	assert (Packet.parse_params("1,,abc=def")[0] is None)
	assert (Packet.parse_params("1,a#c=def")[0] is None)
	assert (Packet.parse_params("1,a:c=d ef")[0] is None)
	assert (Packet.parse_params("1,ac=d ef")[0] is None)

	print("Autotest ok")
