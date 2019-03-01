#!/usr/bin/env python3
# FM demodulator based on I/Q (quadrature) samples

import struct, numpy, sys, math

MAX_DEVIATION = 200000 # Hz
INPUT_RATE = 256000
DEVIATION_X_SIGNAL = 0.99 / (math.pi * MAX_DEVIATION / (INPUT_RATE / 2))

remaining_data = b''

while True:
	# Ingest up to 0.1s worth of data
	data = sys.stdin.buffer.read(INPUT_RATE * 2 // 10)
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

	# find angle (phase) of I/Q pairs
	iqdata = numpy.frombuffer(data, dtype=numpy.uint8)
	iqdata = iqdata - 127.5
	iqdata = iqdata / 128.0
	iqdata = iqdata.view(complex)

	angles = numpy.angle(iqdata)

	# Determine phase rotation between samples
	# (Output one element less, that's we always save last sample
	# in remaining_data)
	rotations = numpy.ediff1d(angles)

	# Wrap rotations >= +/-180º
	rotations = (rotations + numpy.pi) % (2 * numpy.pi) - numpy.pi

	# Convert rotations to baseband signal 
	output_raw = numpy.multiply(rotations, DEVIATION_X_SIGNAL)
	output_raw = numpy.clip(output_raw, -0.999, +0.999)

	# Scale to signed 16-bit int
	output_raw = numpy.multiply(output_raw, 32767)
	output_raw = output_raw.astype(int)

	# Missing: low-pass filter and deemphasis filter
	# (result may be noisy)

	# Output as raw 16-bit, 1 channel audio
	bits = struct.pack(('<%dh' % len(output_raw)), *output_raw)

	sys.stdout.buffer.write(bits)
