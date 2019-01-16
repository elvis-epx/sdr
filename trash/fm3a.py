#!/usr/bin/env python3

# FM demodulator based on I/Q (quadrature)

import wave, struct, math, random, sys, filters, numpy

MAX_DEVIATION = 300000.0 # Hz
INPUT_RATE = 256000
STEREO_CARRIER = 38000 # Hz
FM_BANDWIDTH = 15000 # Hz
DEVIATION_X_SIGNAL = 0.999 / (math.pi * MAX_DEVIATION / INPUT_RATE)

# Low-pass filter for mono (L+R) audio
lo = filters.lowpass(INPUT_RATE, FM_BANDWIDTH)
# High-pass filter for stereo (L-R) modulated audio
hi = filters.bandpass(INPUT_RATE, STEREO_CARRIER - FM_BANDWIDTH, STEREO_CARRIER + FM_BANDWIDTH)
# Low-pass filter for joint-stereo demodulated audio (L-R)
lo_r = filters.lowpass(INPUT_RATE, FM_BANDWIDTH)
# Filters to detect stereo pilot tone
pilot = filters.bandpass(INPUT_RATE, STEREO_CARRIER / 2 - 50, STEREO_CARRIER / 2 + 50)

w = 2 * math.pi
pll = math.pi - random.random() * w
last_pilot = 0.0
deviation_avg = math.pi - random.random() * w
last_deviation_avg = deviation_avg

last_iq = 0.0
remaining_data = b''

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
	rotations = ( rotations + numpy.pi) % ( 2 * numpy.pi ) - numpy.pi

	# Convert angle change to baseband signal strength
	output_raw = numpy.multiply(rotations, DEVIATION_X_SIGNAL)
	output_raw = numpy.clip(output_raw, -0.999, +0.999)

	# At this point, output_raw contains two audio signals:
	# L+R (mono-compatible) and L-R (joint-stereo) modulated in AM-SC,
	# carrier 38kHz

	# Extract L+R (mono) signal by low-pass filtering raw at 15kHz
	output_mono = lo.feed(output_raw)

	# Filter pilot tone
	detected_pilot = pilot.feed(output_raw)

	# Separate modulated L-R signal by high-pass filtering
	output_jstereo_mod = hi.feed(output_raw)

	# Demodulate L-R
	output_jstereo = []

	for n in range(0, len(output_jstereo_mod)):
		# Advance carrier
		pll = (pll + w * STEREO_CARRIER / INPUT_RATE) % w

		while pll > w:
			pll -= w

		# Standard demodulation
		output_jstereo.append(math.cos(pll) * output_jstereo_mod[n])

		# Detect pilot zero-crossing
		cur_pilot = detected_pilot[n]
		zero_crossed = (cur_pilot * last_pilot) <= 0
		last_pilot = cur_pilot
		if not zero_crossed:
			continue

		# When pilot is at 90º or 270º, carrier should be around 180º
		# t=0    => cos(t) = 1,  cos(2t) = 1
		# t=π/2  => cos(t) = 0,  cos(2t) = -1
		# t=π    => cos(t) = -1, cos(2t) = 1
		# t=-π/2 => cos(t) = 0,  cos(2t) = -1
		ideal = math.pi
		deviation = pll - ideal
		if deviation > math.pi:
			# 350º => -10º
			deviation -= w
		deviation_avg = 0.99 * deviation_avg + 0.01 * deviation
		rotation = deviation_avg - last_deviation_avg
		last_deviation_avg = deviation_avg

		if abs(deviation_avg) > math.pi / 8:
			# big phase deviation, reset PLL
			# print("Resetting PLL")
			pll = ideal
			pll = (pll + w * STEREO_CARRIER / INPUT_RATE) % w
			deviation_avg = 0.0
			last_deviation_avg = 0.0
		
		STEREO_CARRIER -= rotation * 200
		'''
		print("%d deviationavg=%f rotation=%f freq=%f" %
			(n,
			deviation_avg * 180 / math.pi,
			rotation * 180 / math.pi,
			STEREO_CARRIER))
		'''
	
	# Low-pass demodulated L-R to remove artifacts
	output_jstereo = lo_r.feed(output_jstereo)
	assert len(output_jstereo) == len(output_mono)

	output_samples = []
	# Output stereo by adding or subtracting joint-stereo to mono
	for n in range(0, len(output_mono)):
		# Left = (Left + Right) + (Left - Right)
		output_samples.append((output_mono[n] + output_jstereo[n]) / 2)
		# Right = (Left + Right) - (Left - Right)
		output_samples.append((output_mono[n] - output_jstereo[n]) / 2)
		
	output_samples = [ int(o * 32767) for o in output_samples ]
	sys.stdout.buffer.write(struct.pack(('%dh' % len(output_samples)), *output_samples))
