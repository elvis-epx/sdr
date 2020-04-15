#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, math, asyncio
from sim_radio import Radio
from sim_network import Station, run
from sim_trafficgen import *

STATION_COUNT=5

stations = {}
r = Radio()

# create stations
for i in range(0, STATION_COUNT):
	callsign = chr(ord('A') + i) * 4
	stations[callsign] = Station(callsign, r)

r.edge("BBBB", "AAAA", -40) 
r.edge("CCCC", "BBBB", -70) 
r.edge("DDDD", "CCCC", -65)
r.edge("EEEE", "DDDD", -65)
r.edge("AAAA", "EEEE", -65)

for callsign, station in stations.items():
	for c in traffic_gens:
		station.add_traffic_gen(c)
	pass

run()
