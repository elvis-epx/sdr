#!/usr/bin/env python3

# Estimate signal strengh

import struct, numpy, sys, math, filters

gain = float(sys.argv[1])

INPUT_RATE = 960000
FPS = 10
BANDWIDTH = 240000
IF_RATE = BANDWIDTH

SAMPLE_US = 1000000 / IF_RATE

remaining_data = b''

if_filter = filters.low_pass(INPUT_RATE, BANDWIDTH / 2, 48)
if_decimator = filters.decimator(INPUT_RATE // IF_RATE)

bgnoise = 0.66 / 128 # 2/3 of one bit
ook_threshold_db_up = 10 # dB above background noise
ook_threshold_db_down = 8
ook_threshold_mul_up = 10 ** (ook_threshold_db_up / 10)
ook_threshold_mul_down = 10 ** (ook_threshold_db_down / 10)

state = 0
length = 0

while True:
    # Ingest up to 1/FPS worth of data
    data = sys.stdin.buffer.read(INPUT_RATE * 2 // FPS)
    if not data:
        break
    data = remaining_data + data
    remaining_data = b''

    if len(data) < 4:
        remaining_data = data
        continue

    # Parse RTL-SDR I/Q format
    iqdata = numpy.frombuffer(data, dtype=numpy.uint8)
    iqdata = iqdata - 127.4
    iqdata = iqdata / 128.0
    iqdata = iqdata.view(complex)

    # Filter and downsample to bandwidth of interest
    iqdata = if_filter.feed(iqdata)
    iqdata = if_decimator.feed(iqdata)

    # We are only interested in absolute amplitude
    iqdata = numpy.absolute(iqdata)

    # Calculate background noise & moving average
    totenergy = numpy.sum(iqdata)
    counter = len(iqdata)
    avg = totenergy / counter
    bgnoise = bgnoise * 0.999 + avg * 0.001
    ook_threshold_up = bgnoise * ook_threshold_mul_up
    ook_threshold_down = bgnoise * ook_threshold_mul_down
    print("bgnoise %f %f" % (bgnoise, avg))

    for sample in iqdata:
        if state == 0:
            if sample > ook_threshold_up:
                print("-%d", int(length * SAMPLE_US))
                length = 0
                state = 1
        else:
            if sample < ook_threshold_down:
                print("+%d", int(length * SAMPLE_US))
                length = 0
                state = 0
        length += 1
