#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys, string, time
from sim_network import Station

loop = asyncio.get_event_loop()

class RagChewer:
	def __init__(self, station):
		async def talk():
			while True:
				await asyncio.sleep(60 * random.random())
				to_options = Station.get_all_callsigns()
				# to_options.remove(station.callsign)
				to_options.append("UNKNOWN")
				to_options.append("QC")
				to_options.append("QL")
				to = random.choice(to_options)
				msg = ''.join(random.choice("     " + string.ascii_lowercase + string.digits) \
					for _ in range(20))
				params = {}
				if random.random() < 0.1:
					params["T"] = int(time.time()) - 1552265462
				if random.random() < 0.1:
					params["S"] = "de4db33f"

				station.send(to, params, msg)
		loop.create_task(talk())

class Pinger:
	def __init__(self, station):
		async def talk():
			while True:
				await asyncio.sleep(150 * random.random())
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
				await asyncio.sleep(600 * random.random())
				to_options = Station.get_all_callsigns()
				to = random.choice(to_options)
				msg = ''.join(random.choice("     " + string.ascii_lowercase + string.digits) \
					for _ in range(3))

				station.send(to, {"RREQ": None}, msg)
		loop.create_task(talk())

traffic_gens = [ RagChewer, Pinger, TraceRouter ]
