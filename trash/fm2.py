#!/usr/bin/env python3

# FM demodulator based on I/Q (quadrature)

import wave, struct, math, random, sys

MAX_DEVIATION = 300000.0 # Hz
INPUT_RATE = 256000

last_angle = 0.0
last_output = 0
remaining_data = b''
total = 0
toasted = 0

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

	for n in range(0, samples):
		i = (data[n * 2] - 127.5) / 128.0
		q = (data[n * 2 + 1] - 127.5) / 128.0
		total += 1

		# Determine phase (angle) of I/Q pair
		angle = math.atan2(q, i)
	
		# Change of angle = baseband signal
		# Were you rushing or were you dragging?!
		angle_change = last_angle - angle
		if angle_change > math.pi:
			angle_change -= 2 * math.pi
		elif angle_change < -math.pi:
			angle_change += 2 * math.pi
		last_angle = angle
	
		# Convert angle change to baseband signal strength
		output = angle_change / (math.pi * MAX_DEVIATION / INPUT_RATE)
		if abs(output) >= 1:
			# some unexpectedly big angle change happened
			toasted += 1
			output = last_output
		output_samples.append(output)

		last_output = output
		
	output_samples = [ int(o * 32767) for o in output_samples ]
	sys.stdout.buffer.write(struct.pack(('%dh' % len(output_samples)), *output_samples))
