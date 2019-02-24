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
				await asyncio.sleep(20 + random.random() * 30)
				to_options = Station.get_all_callsigns()
				to_options.remove(station.callsign)
				to = random.choice(to_options)
				msg = ''.join(random.choice(string.ascii_lowercase + string.digits) \
					for _ in range(5))

				station.send(to, "bla bla " + msg)
		loop.create_task(talk())
