#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

# Automatic handlers for certain application protocols

import random, asyncio, sys, string

loop = asyncio.get_event_loop()

class Ping:
	@staticmethod
	def match(pkt):
		return "PING" in pkt.params and len(pkt.to) > 2

	def __init__(self, station, pkt):
		who = pkt.fr0m
		msg = pkt.msg
		station.send(who, {"PONG": None}, msg)

class Rreq:
	@staticmethod
	def match(pkt):
		return "RREQ" in pkt.params and len(pkt.to) > 2

	def __init__(self, station, pkt):
		who = pkt.fr0m
		msg = pkt.msg + "\n"
		station.send(who, {"RRSP": None}, msg)

app_handlers = [ Ping, Rreq ]
