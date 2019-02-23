#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, math, asyncio, knitter

STATION_COUNT=10

stations = {}
r = knitter.radio()

# create stations
for i in range(0, STATION_COUNT):
	callsign = chr(ord('A') + i)
	stations[callsign] = knitter.Station(callsign, r)

# create model mesh
r.edge("A", "B", -50)  # "A" <- "B", rssi -50
r.edge("A", "C", -70)

r.edge("C", "A", -60)
r.edge("C", "B", -75)
r.edge("C", "E", -80)
r.edge("C", "F", -60)

r.edge("B", "A", -55)
r.edge("B", "C", -75)
r.edge("B", "D", -51)
r.edge("B", "E", -51)

r.edge("D", "B", -45)
r.edge("D", "E", -65)
r.edge("D", "G", -85)

r.edge("E", "B", -70)
r.edge("E", "C", -60)
r.edge("E", "D", -90)
r.edge("E", "F", -120) # out
r.edge("E", "G", -65)
r.edge("E", "H", -62)

r.edge("F", "C", -120) # out
r.edge("F", "E", -120) # out
r.edge("F", "H", -80) 

r.edge("G", "D", -61)
r.edge("G", "E", -62)
r.edge("G", "H", -63)
r.edge("G", "I", -119) # out

r.edge("H", "F", -120) # out
r.edge("H", "E", -66) 
r.edge("H", "G", -60) 
r.edge("H", "I", -47) 

r.edge("I", "G", -40) 
r.edge("I", "H", -70) 
r.edge("I", "J", -65)

r.edge("J", "I", -60) 

# add talkers
for callsign, station in stations.items():
	# station.add(Beacon).add(RagChewer).add(MeshFormation)
	station.add(knitter.MeshFormation)

knitter.run()
