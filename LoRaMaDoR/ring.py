#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, math, asyncio
from sim_radio import Radio
from sim_network import Station, ttl, run
from sim_trafficgen import *
from sim_router_edge import Router

STATION_COUNT=5

stations = {}
r = Radio()

# create stations
for i in range(0, STATION_COUNT):
	callsign = chr(ord('A') + i)
	stations[callsign] = Station(callsign, r, Router)

r.edge("B", "A", -40) 
r.edge("C", "B", -70) 
r.edge("D", "C", -65)
r.edge("E", "D", -65)
r.edge("A", "E", -65)

for callsign, station in stations.items():
	station.add_traffic_gen(RagChewer)
	pass

ttl(4)
run()
