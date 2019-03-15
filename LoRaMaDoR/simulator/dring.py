#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, math, asyncio
from sim_radio import Radio
from sim_network import Station, ttl, run
from sim_router import Router
from sim_mapper import Mapper
from sim_trafficgen import *

STATION_COUNT = 5

stations = {}
r = Radio()

# create stations
for i in range(0, STATION_COUNT):
	callsign = chr(ord('A') + i)
	stations[callsign] = Station(callsign, r, Router, Mapper)

r.biedge("B", "A", -40, -45) 
r.biedge("C", "B", -70, -60) 
r.biedge("D", "C", -70, -60) 
r.biedge("E", "D", -70, -60) 
r.biedge("A", "E", -70, -60) 

for callsign, station in stations.items():
	station.add_traffic_gen(RagChewer)
	pass

ttl(2)
run()
