#!/usr/bin/env python3

import struct, numpy, sys, math, wave, filters

INPUT_RATE = 256000

'''
MAX_DEVIATION = 10000 # Hz
CENTER=462637500
freqs = [462562500, 462587500, 462612500, 462637500, 462662500, 462687500, 462712500,
	 462550000, 462575000, 462600000, 462625000, 462650000, 462675000, 462675000,
	 462725000]
AUDIO_BANDWIDTH = 3400
IF_BANDWIDTH = 20000
AUDIO_RATE = 8000
'''

MAX_DEVIATION = 200000 # Hz
CENTER = 93100000
freqs = [93100000]
IF_BANDWIDTH = 250000
AUDIO_BANDWIDTH = 15000
AUDIO_RATE = 32000

assert (INPUT_RATE // AUDIO_RATE) == (INPUT_RATE / AUDIO_RATE)

DEVIATION_X_SIGNAL = 0.99 / (math.pi * MAX_DEVIATION / (INPUT_RATE / 2))

tau = 2 * math.pi

class Demodulator:
	def __init__(self, freq):
		self.freq = freq
		self.wav = wave.open("%d.wav" % freq, "w")
		self.wav.setnchannels(1)
		self.wav.setsampwidth(1)
		self.wav.setframerate(AUDIO_RATE)
		# since samples are complex, filter goes from -freq to +freq
		self.if_filter = filters.low_pass(INPUT_RATE, IF_BANDWIDTH / 2, 48)
		# real samples, filter goes from 0 to +freq
		self.audio_filter = filters.band_pass(INPUT_RATE, 30, AUDIO_BANDWIDTH, 24)
		self.decimator = filters.decimator(INPUT_RATE // AUDIO_RATE)
		self.if_freq = freq - CENTER
		self.if_angle = 0
		self.last_if_sample = []

	def ingest(self, iqsamples):
		# Center frequency of samples on desired frequency
		ifsamples = []
		for i in range(0, len(iqsamples)):
			self.if_angle = (self.if_angle + tau * self.if_freq / INPUT_RATE) % tau
			if_carrier = math.cos(self.if_angle)
			if_carrier = 1
			ifsamples.append(if_carrier * iqsamples[i])

		# Get last sample from last batch
		ifsamples = self.last_if_sample + ifsamples

		# Filter IF to bandwidth
		# ifsamples = self.if_filter.feed(ifsamples)

		# Save last sample to next batch
		self.last_if_sample = ifsamples[-1:]

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

		# Filter audio to bandwidth and decimate
		output_raw = self.audio_filter.feed(output_raw)
		output_raw = self.decimator.feed(output_raw)

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
# prefilter = filters.low_pass(INPUT_RATE, 400000, 24)
# prefilter = filters.low_pass(INPUT_RATE, 100000, 24)

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
		# d.ingest(prefilter.feed(iqdata))
		d.ingest(iqdata)
