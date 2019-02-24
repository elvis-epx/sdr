#!/usr/bin/env python3

import struct, numpy, sys, math, wave, filters

INPUT_RATE = 960000

'''
MAX_DEVIATION = 10000 # Hz
CENTER=462637500
freqs = [462562500, 462587500, 462612500, 462637500, 462662500, 462687500, 462712500,
	 462550000, 462575000, 462600000, 462625000, 462650000, 462675000, 462675000,
	 462725000]
IF_BANDWIDTH = 20000
IF_RATE = 40000
AUDIO_BANDWIDTH = 3400
AUDIO_RATE = 8000
'''

MAX_DEVIATION = 200000 # Hz
CENTER = 92900000
freqs = [93100000]
IF_BANDWIDTH = 200000
IF_RATE = 240000
AUDIO_BANDWIDTH = 15000
AUDIO_RATE = 48000

assert (INPUT_RATE // IF_RATE) == (INPUT_RATE / IF_RATE)
assert (IF_RATE // AUDIO_RATE) == (IF_RATE / AUDIO_RATE)

DEVIATION_X_SIGNAL = 0.99 / (math.pi * MAX_DEVIATION / (IF_RATE / 2))

tau = 2 * math.pi

class Demodulator:
	def __init__(self, freq):
		self.freq = freq
		self.wav = wave.open("%d.wav" % freq, "w")
		self.wav.setnchannels(1)
		self.wav.setsampwidth(1)
		self.wav.setframerate(AUDIO_RATE)

		# IF control
		self.if_freq = CENTER - freq
		self.if_angle = 0
		self.if_adv = tau * self.if_freq / INPUT_RATE
		self.last_if_sample = []

		# IF filtering
		# complex samples, filter goes from -freq to +freq
		self.if_filter = filters.low_pass(INPUT_RATE, IF_BANDWIDTH / 2, 48)
		self.if_decimator = filters.decimator(INPUT_RATE // IF_RATE)

		# Audio filter
		self.audio_filter = filters.band_pass(IF_RATE, 30, AUDIO_BANDWIDTH, 24)
		self.audio_decimator = filters.decimator(IF_RATE // AUDIO_RATE)


	def ingest(self, iqsamples):
		# Center frequency of samples on desired frequency
		ifsamples = []
		for i in range(0, len(iqsamples)):
			self.if_angle = (self.if_angle + self.if_adv) % tau
			if_carrier = math.cos(self.if_angle)
			ifsamples.append(if_carrier * iqsamples[i])

		# Get last sample from last batch
		ifsamples = self.last_if_sample + ifsamples

		# Save last sample to next batch
		self.last_if_sample = ifsamples[-1:]

		# Filter IF to radio bandwidth and decimate
		ifsamples = self.if_filter.feed(ifsamples)
		ifsamples = self.if_decimator.feed(ifsamples)

		# Finds angles (phase) of I/Q pairs
		angles = numpy.angle(ifsamples)
	
		# Determine phase rotation between samples
		# (Output one element less, that's we always save last sample
		# in remaining_data)
		rotations = numpy.ediff1d(angles)

		# Wrap rotations >= +/-180º
		rotations = (rotations + numpy.pi) % (2 * numpy.pi) - numpy.pi
	
		# Convert rotations to baseband signal 
		output_raw = numpy.multiply(rotations, DEVIATION_X_SIGNAL)
		output_raw = numpy.clip(output_raw, -0.999, +0.999)

		# Filter to audio bandwidth and decimate
		output_raw = self.audio_filter.feed(output_raw)
		output_raw = self.audio_decimator.feed(output_raw)

		# Scale to unsigned 8-bit int with offset (8-bit WAV)
		output_raw = numpy.multiply(output_raw, 127) + 127
		output_raw = output_raw.astype(int)
	
		bits = struct.pack('%dB' % len(output_raw), *output_raw)
		self.wav.writeframes(bits)

demodulators = {}
for freq in freqs:
	demodulators[freq] = Demodulator(freq)

# Prefilter to get 200kHz out of 1M band
# Complex samples, bandwidth goes from -freq to +freq
prefilter = filters.low_pass(INPUT_RATE, 400000, 24)

remaining_data = b''
	
while True:
	# Ingest up to 0.1s worth of data
	data = sys.stdin.buffer.read(INPUT_RATE * 2 // 10)
	if not data:
		break
	data = remaining_data + data

	# Save odd byte
	if len(data) % 2 == 1:
		print("Odd byte, that's odd", file=sys.stderr)
		remaining_data = data[-1:]
		data = data[:-1]

	# Convert to complex numbers
	iqdata = [ ((data[n * 2 + 0] - 127.5) + (0+1j) * (data[n * 2 + 1] - 127.5)) / 128.0
		for n in range(0, len(data) // 2) ]

	# Forward I/Q samples to all channels
	for k, d in demodulators.items():
		d.ingest(prefilter.feed(iqdata))
