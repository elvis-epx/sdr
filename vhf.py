#!/usr/bin/env python3

import struct, numpy, sys, math, wave, filters, time, datetime

INPUT_RATE = 1000000

MAX_DEVIATION = 10000 # Hz
CENTER = 152500000 
freqs = [152390000]
STEP = 2500
IF_BANDWIDTH = 20000
IF_RATE = 25000
AUDIO_BANDWIDTH = 4000
AUDIO_RATE = 12500

# -45..-48 dbFS is the minimum, 6db = 1 bit of audio
THRESHOLD = -39

assert (INPUT_RATE // IF_RATE) == (INPUT_RATE / IF_RATE)
assert (IF_RATE // AUDIO_RATE) == (IF_RATE / AUDIO_RATE)

# Makes sure IF demodulation carrier will be a multiple of STEP Hz
assert (INPUT_RATE / STEP == INPUT_RATE // STEP)
for f in freqs:
	if_freq = abs(CENTER - f)
	assert(if_freq / STEP == if_freq // STEP)

DEVIATION_X_SIGNAL = 0.99 / (math.pi * MAX_DEVIATION / (IF_RATE / 2))

tau = 2 * math.pi

class Demodulator:
	def __init__(self, freq):
		self.freq = freq
		self.wav = wave.open("%d.wav" % freq, "w")
		self.wav.setnchannels(1)
		self.wav.setsampwidth(1)
		self.wav.setframerate(AUDIO_RATE)
		self.recording = False

		# Energy estimation
		self.energy = -48

		# IF
		self.if_freq = CENTER - freq
		# works because both if_freq and INPUT_RATE are multiples of STEP
		self.carrier_table = [ math.cos(t * tau * (self.if_freq / INPUT_RATE))
				for t in range(0, INPUT_RATE // 4) ]
		self.carrier_table = numpy.array(self.carrier_table)
		# actually, this is the biggest period (carrier of 2500Hz)
		self.if_period = INPUT_RATE // STEP
		self.if_phase = 0
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

		# Get a cosine table in correct phase
		carrier = self.carrier_table[self.if_phase:self.if_phase + len(iqsamples)]
		# Advance phase
		self.if_phase = (self.if_phase + len(iqsamples)) % self.if_period
		# Demodulate
		ifsamples = iqsamples * carrier

		# Filter IF to radio bandwidth and decimate
		ifsamples = self.if_filter.feed(ifsamples)
		ifsamples = self.if_decimator.feed(ifsamples)

		# Get last sample from last batch
		ifsamples = self.last_if_sample + ifsamples

		# Save last sample to next batch
		self.last_if_sample = ifsamples[-1:]

		# Finds angles (phase) of I/Q pairs
		angles = numpy.angle(ifsamples)

		# Average signal strengh
		energy = numpy.sum(numpy.absolute(ifsamples)) \
			* math.sqrt(INPUT_RATE / IF_RATE) \
			/ len(ifsamples)
		db = 20 * math.log10(energy)
		self.energy = 0.5 * db + 0.5 * self.energy

		# print("%f: signal %f dbFS" % (self.freq, self.energy))
		if not self.recording:
			if self.energy > THRESHOLD:
				print("%s %f: signal %f dbFS, recording" % \
					(str(datetime.datetime.now()), self.freq, self.energy))
				self.recording = True
		else:
			if self.energy < THRESHOLD:
				print("%s %f: signal %f dbFS, stopping tape" % \
					(str(datetime.datetime.now()), self.freq, self.energy))
				self.recording = False

		if not self.recording:
			return

		# Determine phase rotation between samples
		# (Output one element less, that's we always save last sample
		# in remaining_data)
		rotations = numpy.ediff1d(angles)

		# Wrap rotations >= +/-180º
		rotations = (rotations + numpy.pi) % (2 * numpy.pi) - numpy.pi
	
		# Convert rotations to baseband signal 
		output_raw = numpy.multiply(rotations, DEVIATION_X_SIGNAL)

		# Filter to audio bandwidth and decimate
		output_raw = self.audio_filter.feed(output_raw)
		output_raw = self.audio_decimator.feed(output_raw)

		# Scale to unsigned 8-bit int with offset (8-bit WAV)
		output_raw = numpy.clip(output_raw, -0.999, +0.999)
		output_raw = numpy.multiply(output_raw, 127) + 127
		output_raw = output_raw.astype(int)
	
		bits = struct.pack('%dB' % len(output_raw), *output_raw)
		self.wav.writeframes(bits)

demodulators = {}
for freq in freqs:
	demodulators[freq] = Demodulator(freq)

# Prefilter to get +/-240kHz out of +/-480kHz band
# Complex samples, bandwidth goes from -freq to +freq
# prefilter = filters.low_pass(INPUT_RATE, 240000, 48)

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
	iqdata = numpy.array(iqdata)

	# Forward I/Q samples to all channels
	for k, d in demodulators.items():
		# d.ingest(prefilter.feed(iqdata))
		d.ingest(iqdata)
