#!/usr/bin/env python3

# FM demodulator based on I/Q (quadrature)

import wave, struct, math, random, sys, filters, numpy

MAX_DEVIATION = 300000.0 # Hz
INPUT_RATE = 256000
DEVIATION_X_SIGNAL = 0.999 / (math.pi * MAX_DEVIATION / INPUT_RATE)

last_angle = 0.0
remaining_data = b''
total = 0

lo = filters.lowpass(INPUT_RATE, 15000)

while True:
	data = sys.stdin.buffer.read(INPUT_RATE * 2 // 10)
	if not data:
		break
	data = remaining_data + data
	if len(data) % 2 == 1:
		remaining_data = data[-1]
		data = data[:-1]
	else:
		remaining_data = b''

	samples = len(data) // 2
	output_samples = []

	i = numpy.array([ (data[n * 2] - 127.5) / 128.0 for n in range(0, samples) ])
	q = numpy.array([ (data[n * 2 + 1] - 127.5) / 128.0 for n in range(0, samples) ])

	# Determine phase (angle) of I/Q pairs
	angles = numpy.arctan2(q, i)

	for angle in angles:
		# Change of angle = baseband signal
		# Were you rushing or were you dragging?!
		angle_change = last_angle - angle
		if angle_change > math.pi:
			angle_change -= 2 * math.pi
		elif angle_change < -math.pi:
			angle_change += 2 * math.pi
		last_angle = angle
	
		# Convert angle change to baseband signal strength
		output = angle_change * DEVIATION_X_SIGNAL
		# print("%f" % output, file=sys.stderr)
		output_samples.append(output)
		
	output_samples = lo.feed(output_samples)
	output_samples = [ int(o * 32767) for o in output_samples ]
	sys.stdout.buffer.write(struct.pack(('%dh' % len(output_samples)), *output_samples))
