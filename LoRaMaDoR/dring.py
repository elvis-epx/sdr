#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, math, asyncio, knitter

STATION_COUNT=3

stations = {}
r = knitter.radio()

# create stations
for i in range(0, STATION_COUNT):
	callsign = chr(ord('A') + i)
	stations[callsign] = knitter.Station(callsign, r)

r.dbledge("B", "A", -40) 
r.dbledge("C", "B", -70) 
# r.dbledge("D", "C", -65)
# r.dbledge("E", "D", -65)
# r.dbledge("A", "E", -65)

for callsign, station in stations.items():
	# station.add(Beacon).add(RagChewer).add(MeshFormation)
	station.add(knitter.MeshFormation)

knitter.run()
