#!/usr/bin/env python3

# LoRaMaDoR (LoRa-based mesh network for hams) project
# Mesh network simulator / routing algorithms testbed
# Copyright (c) 2019 PU5EPX

import random, math, asyncio
from sim_radio import Radio
from sim_network import Station, run
from sim_trafficgen import *

STATION_COUNT=10

stations = {}
r = Radio()

# create stations
for i in range(0, STATION_COUNT):
	callsign = chr(ord('A') + i) * 5
	stations[callsign] = Station(callsign, r)

# create model mesh
r.edge("AAAAA", "BBBBB", -50)  # "AAAAA" <- "BBBBB", rssi -50
r.edge("AAAAA", "CCCCC", -70)

r.edge("CCCCC", "AAAAA", -60)
r.edge("CCCCC", "BBBBB", -75)
r.edge("CCCCC", "EEEEE", -80)
r.edge("CCCCC", "FFFFF", -60)

r.edge("BBBBB", "AAAAA", -55)
r.edge("BBBBB", "CCCCC", -75)
r.edge("BBBBB", "DDDDD", -51)
r.edge("BBBBB", "EEEEE", -51)

r.edge("DDDDD", "BBBBB", -45)
r.edge("DDDDD", "EEEEE", -65)
r.edge("DDDDD", "GGGGG", -85)

r.edge("EEEEE", "BBBBB", -70)
r.edge("EEEEE", "CCCCC", -60)
r.edge("EEEEE", "DDDDD", -90)
r.edge("EEEEE", "FFFFF", None) # out
r.edge("EEEEE", "GGGGG", -65)
r.edge("EEEEE", "HHHHH", -62)

r.edge("FFFFF", "CCCCC", None) # out
r.edge("FFFFF", "EEEEE", None) # out
r.edge("FFFFF", "HHHHH", -80) 

r.edge("GGGGG", "DDDDD", -61)
r.edge("GGGGG", "EEEEE", -62)
r.edge("GGGGG", "HHHHH", -63)
r.edge("GGGGG", "IIIII", None) # out

r.edge("HHHHH", "FFFFF", None) # out
r.edge("HHHHH", "EEEEE", -66) 
r.edge("HHHHH", "GGGGG", -60) 
r.edge("HHHHH", "IIIII", -47) 

r.edge("IIIII", "GGGGG", -40) 
r.edge("IIIII", "HHHHH", -70) 
r.edge("IIIII", "JJJJJ", -65)

r.edge("JJJJJ", "IIIII", -60) 

# add talkers
for callsign, station in stations.items():
	station.add_traffic_gen(RagChewer)
	pass

run()
