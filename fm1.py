#!/usr/bin/env python3
# FM demodulator based on I/Q (quadrature)

import struct, numpy, sys, math

MAX_DEVIATION = 300000 # Hz
INPUT_RATE = 256000
DEVIATION_X_SIGNAL = 0.99 / (math.pi * MAX_DEVIATION / INPUT_RATE)

remaining_data = b''

while True:
	# Ingest 0.1s worth of data
	data = sys.stdin.buffer.read((INPUT_RATE * 2) // 10)
	if not data:
		break
	data = remaining_data + data

	if len(data) < 4:
		remaining_data = data
		continue

	# Save one sample to next batch, and the odd byte if exists
	if len(data) % 2 == 1:
		print("Odd byte, that's odd", file=sys.stderr)
		remaining_data = data[-3:]
		data = data[:-1]
	else:
		remaining_data = data[-2:]

	samples = len(data) // 2

	# Finds angles (phase) of I/Q pairs
	angles = [
		math.atan2(
			(data[n * 2 + 0] - 127.5) / 128.0, 
			(data[n * 2 + 1] - 127.5) / 128.0
		) for n in range(0, samples) ]

	# Determine phase rotation between samples
	# (Output one element less, that's we always save last sample
	# in remaining_data)
	rotations = numpy.ediff1d(angles)

	# Wrap rotations >= +/-180º
	rotations = (rotations + numpy.pi) % (2 * numpy.pi) - numpy.pi

	# Convert rotations to baseband signal
	output_raw = numpy.multiply(rotations, DEVIATION_X_SIGNAL)
	output_raw = numpy.clip(output_raw, -0.999, +0.999)

	# Missing: low-pass filter and deemphasis filter
	# (result may be noisy)

	# Output as raw 16-bit, 1 channel audio
	bits = struct.pack(('%dh' % len(output_raw)),
		*[ int(o * 32767) for o in output_raw ])

	sys.stdout.buffer.write(bits)
