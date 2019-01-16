#!/usr/bin/env python3

# FM demodulator based on I/Q (quadrature)

import struct, math, random, sys, numpy
import filters2 as filters

MAX_DEVIATION = 300000.0 # Hz
INPUT_RATE = 240000
OUTPUT_RATE = 48000

FM_BANDWIDTH = 15000 # Hz
STEREO_CARRIER = 38000 # Hz
DEVIATION_X_SIGNAL = 0.999 / (math.pi * MAX_DEVIATION / INPUT_RATE)

pll = math.pi - random.random() * 2 * math.pi
last_pilot = 0.0
deviation_avg = math.pi - random.random() * 2 * math.pi
last_deviation_avg = deviation_avg
w = 2 * math.pi

# Downsample mono audio
downsample1 = filters.decimator(5)

# Deemph + Low-pass filter for mono (L+R) audio
lo = filters.deemph(OUTPUT_RATE, 75, FM_BANDWIDTH, FM_BANDWIDTH + 1000)

# Downsample jstereo audio
downsample2 = filters.decimator(5)

# Deemph + Low-pass filter for joint-stereo demodulated audio (L-R)
lo_r = filters.deemph(OUTPUT_RATE, 75, FM_BANDWIDTH, FM_BANDWIDTH + 1000)

# Band-pass filter for stereo (L-R) modulated audio
hi = filters.bandpass(INPUT_RATE,
	STEREO_CARRIER - FM_BANDWIDTH - 2000, STEREO_CARRIER - FM_BANDWIDTH,
	STEREO_CARRIER + FM_BANDWIDTH, STEREO_CARRIER + FM_BANDWIDTH + 2000)

# Filter to extract pilot signal
pilot = filters.bandpass(INPUT_RATE,
	STEREO_CARRIER / 2 - 1000, STEREO_CARRIER / 2 - 100,
	STEREO_CARRIER / 2 + 100, STEREO_CARRIER / 2 + 1000)

last_angle = 0.0
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

	# At this point, output_raw contains two audio signals:
	# L+R (mono-compatible) and L-R (joint-stereo) modulated in AM-SC,
	# carrier 38kHz
	
	# Downsample and low-pass L+R (mono) signal
	output_mono = downsample1.feed(output_raw)
	output_mono = lo.feed(output_mono)

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
	
	# Downsample, Low-pass/deemphasis demodulated L-R
	output_jstereo = downsample2.feed(output_jstereo)
	output_jstereo = lo_r.feed(output_jstereo)

	assert len(output_jstereo) == len(output_mono)

	output = []
	# Output stereo by adding or subtracting joint-stereo to mono
	for n in range(0, len(output_mono)):
		# Left = (Left + Right) + (Left - Right)
		# Righ = (Left + Right) - (Left - Right)
		mono = output_mono[n]
		jst = output_jstereo[n]
		left = mono + jst
		right = mono - jst
		output.append(max(-1, min(1, left / 2)))
		output.append(max(-1, min(1, right / 2)))

	sys.stdout.buffer.write(struct.pack(('<%dh' % len(output)),
		*[ int(o * 32767) for o in output ] ))
