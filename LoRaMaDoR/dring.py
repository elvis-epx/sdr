#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, math, asyncio
from sim_radio import Radio
from sim_network import Station, ttl, run
from sim_trafficgen import *

STATION_COUNT=3

stations = {}
r = Radio()

# create stations
for i in range(0, STATION_COUNT):
	callsign = chr(ord('A') + i)
	stations[callsign] = Station(callsign, r)

r.biedge("B", "A", -40, -45) 
r.biedge("C", "B", -70, -60) 

for callsign, station in stations.items():
	# station.add(RagChewer)
	pass

ttl(2)
run()
