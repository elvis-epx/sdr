#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, asyncio, sys

loop = asyncio.get_event_loop()


class RagChewer:
	def __init__(self, station):
		async def talk():
			while True:
				await asyncio.sleep(15 + random.random() * 30)
				to_options = list(station.radio.stations.keys())
				to_options.remove(station.callsign)
				to = random.choice(to_options)
				station.send(to, "bla")
		loop.create_task(talk())
