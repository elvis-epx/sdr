#!/usr/bin/env python3

import struct, numpy, sys, math, filters

INPUT_RATE = 960000
BANDWIDTH = 20000
IF_RATE = 20000

remaining_data = b''

counter = 0
totenergy = 0.0
counter2 = 0
totenergy2 = 0.0


if_filter = filters.low_pass(INPUT_RATE, BANDWIDTH / 2, 48)
if_decimator = filters.decimator(INPUT_RATE // IF_RATE)

while True:
	# Ingest up to 0.1s worth of data
	data = sys.stdin.buffer.read(INPUT_RATE * 2 // 10)
	if not data:
		break
	data = remaining_data + data

	if len(data) < 4:
		remaining_data = data
		continue

	# Convert to complex numbers
	iqdata = [ ((data[n * 2 + 0] - 127.5) + (0+1j) * (data[n * 2 + 1] - 127.5)) / 128.0
		for n in range(0, len(data) // 2) ]
	totenergy += numpy.sum(numpy.absolute(iqdata))
	counter += len(iqdata)

	if counter > INPUT_RATE:
		avg = totenergy / counter
		avg = 20 * math.log10(avg)
		print("%f dBFS" % avg)
		counter = 0
		totenergy = 0

	iqdata = if_filter.feed(iqdata)
	iqdata = if_decimator.feed(iqdata)
	totenergy2 += numpy.sum(numpy.absolute(iqdata)) * math.sqrt(INPUT_RATE / IF_RATE)
	counter2 += len(iqdata)

	if counter2 > IF_RATE:
		avg = totenergy2 / counter2
		avg = 20 * math.log10(avg)
		print("narrowband: %f dBFS" % avg)
		counter2 = 0
		totenergy2 = 0
