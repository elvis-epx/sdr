#!/usr/bin/env python3

import struct, numpy, sys, math

INPUT_RATE = 256000

remaining_data = b''

counter = 0
totenergy = 0.0

while True:
	# Ingest up to 0.1s worth of data
	data = sys.stdin.buffer.read(INPUT_RATE * 2 // 10)
	if not data:
		break
	data = remaining_data + data

	if len(data) < 4:
		remaining_data = data
		continue

	# Convert to energy
	energy = [ math.sqrt(((data[n * 2 + 0] - 127.5) / 128.0) ** 2 + ((data[n * 2 + 1] - 127.5) / 128.0) ** 2) \
		for n in range(0, len(data) // 2) ]
	counter += len(energy)
	totenergy += sum(energy)

	if counter > INPUT_RATE:
		avg = totenergy / counter
		avg = 20 * math.log10(avg)
		print("%f dBFS" % avg)
		counter = 0
		totenergy = 0
