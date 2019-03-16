#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, string
from sim_network import Station

loop = asyncio.get_event_loop()

class RagChewer:
	def __init__(self, station):
		async def talk():
			while True:
				await asyncio.sleep(60 * random.random())
				to_options = Station.get_all_callsigns()
				to_options.remove(station.callsign)
				to_options.append("UNKNOWN")
				to = random.choice(to_options)
				msg = ''.join(random.choice("     " + string.ascii_lowercase + string.digits) \
					for _ in range(20))

				station.send(to, {}, msg)
		loop.create_task(talk())

class Pinger:
	def __init__(self, station):
		async def talk():
			while True:
				await asyncio.sleep(60 * random.random())
				to_options = Station.get_all_callsigns()
				to = random.choice(to_options)
				msg = ''.join(random.choice("     " + string.ascii_lowercase + string.digits) \
					for _ in range(3))

				station.send(to, {"PING": None}, msg)
		loop.create_task(talk())

class TraceRouter:
	def __init__(self, station):
		async def talk():
			while True:
				await asyncio.sleep(60 * random.random())
				to_options = Station.get_all_callsigns()
				to = random.choice(to_options)
				msg = ''.join(random.choice("     " + string.ascii_lowercase + string.digits) \
					for _ in range(3))

				station.send(to, {"RREQ": None}, msg)
		loop.create_task(talk())

traffic_gens = [ RagChewer, Pinger, TraceRouter ]
