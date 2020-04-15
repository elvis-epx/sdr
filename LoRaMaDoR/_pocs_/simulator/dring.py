#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, math, asyncio
from sim_radio import Radio
from sim_network import Station, run
from sim_trafficgen import *

STATION_COUNT = 5

stations = {}
r = Radio()

# create stations
for i in range(0, STATION_COUNT):
	callsign = chr(ord('A') + i) * 4
	stations[callsign] = Station(callsign, r)

r.biedge("BBBB", "AAAA", -40, -45) 
r.biedge("CCCC", "BBBB", -70, -60) 
r.biedge("DDDD", "CCCC", -70, -60) 
r.biedge("EEEE", "DDDD", -70, -60) 
r.biedge("AAAA", "EEEE", -70, -60) 

for callsign, station in stations.items():
	station.add_traffic_gen(RagChewer)
	pass

run()
