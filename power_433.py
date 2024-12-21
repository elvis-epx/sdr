#!/usr/bin/env python3

# Estimate signal strengh

import struct, numpy, sys, math

gain = float(sys.argv[1])

INPUT_RATE = 250000
FPS = 100

remaining_data = b''

counter = 0
totenergy = 0.0

while True:
    # Ingest up to 0.01s worth of data
    data = sys.stdin.buffer.read(INPUT_RATE * 2 // FPS)
    if not data:
        break
    data = remaining_data + data
    remaining_data = b''

    if len(data) < 4:
        remaining_data = data
        continue

    iqdata = numpy.frombuffer(data, dtype=numpy.uint8)
    iqdata = iqdata - 127.5
    iqdata = iqdata / 128.0
    iqdata = iqdata.view(complex)

    totenergy += numpy.sum(numpy.absolute(iqdata))
    counter += len(iqdata)

    if counter >= INPUT_RATE // FPS:
        avg = totenergy / counter
        avgdb = 20 * math.log10(avg) - gain
        print("%d %.9f, %f dBFS, %f dBm" % (counter, avg, avgdb + gain, avgdb))
        counter = 0
        totenergy = 0
