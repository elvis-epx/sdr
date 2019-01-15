#!/usr/bin/env python3
# FM demodulator based on I/Q (quadrature)

import wave, struct, numpy, sys, math

MAX_DEVIATION = 300000 # Hz
INPUT_RATE = 256000
DEVIATION_X_SIGNAL = 0.99 / (math.pi * MAX_DEVIATION / INPUT_RATE)

wav = None
if len(sys.argv) > 1:
	wav = wave.open(sys.argv[1], "w")
	wav.setnchannels(1)
	wav.setsampwidth(2)
	wav.setframerate(INPUT_RATE)

last_iq = 0.0
remaining_data = b''

while True:
	data = sys.stdin.buffer.read((INPUT_RATE * 2) // 10)
	if not data:
		break
	data = remaining_data + data
	if len(data) % 2 == 1:
		print("Got odd number of samples")
		remaining_data = data[-1]
		data = data[:-1]
	else:
		remaining_data = b''

	# Group I/Q pairs as complex numbers
	# Prepends last angle from previous round
	samples = len(data) // 2
	iq = [ last_iq ]
	for n in range(0, samples):
		iq.append(complex(
				(data[n * 2] - 127.5) / 128.0, 
				(data[n * 2 + 1] - 127.5) / 128.0))
	last_iq = iq[-1]

	# Find phase (angle) of all I/Q pairs
	angles = numpy.angle(iq)

	# Determine how much phase rotates between samples 
	# len(rotation) = len(angles) - 1
	rotations = numpy.ediff1d(angles)

	# Wrap rotations >= 180º
	rotations = (rotations + numpy.pi) % (2 * numpy.pi) - numpy.pi

	# Convert rotations to baseband signal
	output = numpy.multiply(rotations, DEVIATION_X_SIGNAL)
	output = numpy.clip(output, -0.999, +0.999)

	# Output as 16-bit, 1 channel audio
	bits = struct.pack(('%dh' % len(output)),
				*[ int(o * 32767) for o in output ])
	if wav:
		wav.writeframes(bits)
	else:
		sys.stdout.buffer.write(bits)
