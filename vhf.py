#!/usr/bin/env python3

import struct, numpy, sys, math, wave, filters, time, datetime
import queue, threading

monitor_strength = "-e" in sys.argv

INPUT_RATE = 1000000

INGEST_SIZE = INPUT_RATE // 10

MAX_DEVIATION = 10000 # Hz
CENTER = 153000000
freqs = [152772500]

CENTER = 462500000
freqs = [462562500, 462587500, 462612500, 462637500, 462662500, 462687500, 462712500,
	 462550000, 462575000, 462600000, 462625000, 462650000, 462675000, 462725000]
STEP = 2500
IF_BANDWIDTH = 20000
IF_RATE = 25000
AUDIO_BANDWIDTH = 3400
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
		self.ecount = 0

		# IF
		self.if_freq = CENTER - freq
		# works because both if_freq and INPUT_RATE are multiples of STEP
		self.carrier_table = [ math.cos(t * tau * (self.if_freq / INPUT_RATE))
				for t in range(0, INGEST_SIZE * 2) ]
		self.carrier_table = numpy.array(self.carrier_table)
		# actually, this is the biggest period (carrier of 2500Hz)
		self.if_period = INPUT_RATE // STEP
		self.if_phase = 0
		self.last_if_sample = numpy.array([])

		# IF filtering
		# complex samples, filter goes from -freq to +freq
		self.if_filter = filters.low_pass(INPUT_RATE, IF_BANDWIDTH / 2, 24)
		self.if_decimator = filters.decimator(INPUT_RATE // IF_RATE)

		# Audio filter
		self.audio_filter = filters.band_pass(IF_RATE, 300, AUDIO_BANDWIDTH, 18)
		self.audio_decimator = filters.decimator(IF_RATE // AUDIO_RATE)

		# Thread
		def worker():
			while True:
				iqsamples = self.queue.get()
				if iqsamples is None:
					break
				self._ingest(iqsamples)
				self.queue.task_done()

		self.queue = queue.Queue()
		self.thread = threading.Thread(target=worker)
		self.thread.start()

	def close_queue(self):
		self.queue.put(None)

	def drain_queue(self):
		self.thread.join()

	def ingest(self, iqsamples):
		self.queue.put(iqsamples)

	def _ingest(self, iqsamples):
		self.tmbase = time.time()

		# Center frequency of samples on desired frequency

		# Get a cosine table in correct phase
		carrier = self.carrier_table[self.if_phase:self.if_phase + len(iqsamples)]
		# Advance phase
		self.if_phase = (self.if_phase + len(iqsamples)) % self.if_period
		# Demodulate
		ifsamples = iqsamples * carrier
		# print("%s %f" % ('f demod', time.time() - self.tmbase))

		# Filter IF to radio bandwidth and decimate
		ifsamples = self.if_filter.feed(ifsamples)
		ifsamples = self.if_decimator.feed(ifsamples)
		# print("%s %f" % ('f filter', time.time() - self.tmbase))

		# Get last sample from last batch
		ifsamples = numpy.concatenate((self.last_if_sample, ifsamples))

		# Save last sample to next batch
		self.last_if_sample = ifsamples[-1:]

		# Finds angles (phase) of I/Q pairs
		angles = numpy.angle(ifsamples)
		# print("%s %f" % ('f angle', time.time() - self.tmbase))

		# Average signal strengh
		energy = numpy.sum(numpy.absolute(ifsamples)) \
			* math.sqrt(INPUT_RATE / IF_RATE) \
			/ len(ifsamples)
		db = 20 * math.log10(energy)
		self.energy = 0.5 * db + 0.5 * self.energy
		self.ecount = (self.ecount + 1) % 10
		# print("%s %f" % ('f energy', time.time() - self.tmbase))

		if monitor_strength and self.ecount == 0:
			print("%f: signal %f dbFS" % (self.freq, self.energy))
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
		# print("%s %f" % ('f rotations', time.time() - self.tmbase))

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
		# print("%s %f" % ('f wav', time.time() - self.tmbase))

demodulators = {}
for freq in freqs:
	demodulators[freq] = Demodulator(freq)

# Prefilter to get +/-240kHz out of +/-480kHz band
# Complex samples, bandwidth goes from -freq to +freq
# prefilter = filters.low_pass(INPUT_RATE, 240000, 48)

remaining_data = b''

while True:
	# Ingest data
	data = sys.stdin.buffer.read(INGEST_SIZE * 2)
	if not data:
		break
	data = remaining_data + data

	tmbase = time.time()

	# Save odd byte
	if len(data) % 2 == 1:
		print("Odd byte, that's odd", file=sys.stderr)
		remaining_data = data[-1:]
		data = data[:-1]

	# Convert to complex numbers
	iqdata = numpy.frombuffer(data, dtype=numpy.uint8)
	iqdata = iqdata - 127.5
	iqdata = iqdata / 128.0
	iqdata = iqdata.view(complex)

	iqdata = numpy.array(iqdata)

	# Forward I/Q samples to all channels
	for k, d in demodulators.items():
		d.ingest(iqdata)

for k, d in demodulators.items():
	d.close_queue()

for k, d in demodulators.items():
	d.drain_queue()
