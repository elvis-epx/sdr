#!/usr/bin/env python3

# Multi-channel narrowband FM demodulator for VHF, UHF, Talkabout, etc.
#
# Requisites: - all channels must be within 80% of the raw I/Q bandwidth
#             - the computer must have enough CPU
#               (use less channels, or batch process the I/Q samples,
#               in case your computer can't demodulate in real-time)
#             - Center frequency, bandwidth and channels must be all
#               multiples of STEP.

import struct, numpy, sys, math, wave, filters, time, datetime
import queue, threading

monitor_strength = "-e" in sys.argv
use_autocorrelation = "-a" in sys.argv

INPUT_RATE = int(sys.argv[2])

INGEST_SIZE = INPUT_RATE // 10

MAX_DEVIATION = 5000 # Hz

CENTER=int(sys.argv[1])

freqs = []

for i in range(3, len(sys.argv)):
	if sys.argv[i] == ".":
		break
	freqs.append(int(sys.argv[i]))

STEP = 2500
IF_BANDWIDTH = 10000
IF_RATE = 25000
AUDIO_BANDWIDTH = 3400
AUDIO_RATE = 12500

THRESHOLD_SNR = 9 # 9dB SNR = 1.5 bit
THRESHOLD_AC = 0.2
HISTERESIS = 2

assert (INPUT_RATE // IF_RATE) == (INPUT_RATE / IF_RATE)
assert (IF_RATE // AUDIO_RATE) == (IF_RATE / AUDIO_RATE)

# Makes sure IF demodulation carrier will be a multiple of STEP Hz 
# and it is in bandwidth range (80% of INPUT_RATE)
assert (INPUT_RATE / STEP == INPUT_RATE // STEP)
for f in freqs:
	if_freq = abs(CENTER - f)
	assert(if_freq / STEP == if_freq // STEP)
	assert(if_freq < (0.4 * INPUT_RATE))

DEVIATION_X_SIGNAL = 0.99 / (math.pi * MAX_DEVIATION / (IF_RATE / 2))

tau = 2 * math.pi

class Demodulator:
	def __init__(self, freq):
		self.freq = freq
		self.wav = None
		self.recording = 0

		# Energy estimation
		self.energy_avg = None
		self.energy_off = 0
		self.ecount = 0

		# Autocorrelation average
		self.ac_avg = None

		# IF
		self.if_freq = CENTER - freq
		# works because both if_freq and INPUT_RATE are multiples of STEP
		self.carrier_table = [ math.cos(t * tau * (self.if_freq / INPUT_RATE))
				for t in range(0, INGEST_SIZE * 2) ]
		self.carrier_table = numpy.array(self.carrier_table)
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

	def create_wav(self):
		self.wav = wave.open("%d.wav" % self.freq, "w")
		self.wav.setnchannels(1)
		self.wav.setsampwidth(1)
		self.wav.setframerate(AUDIO_RATE)

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
		energy = 20 * math.log10(energy)

		if self.energy_avg is None:
			self.energy_avg = energy
		else:
			self.energy_avg = 0.03 * energy + 0.97 * self.energy_avg

		self.ecount = (self.ecount + 1) % 25
		# print("%s %f" % ('f energy', time.time() - self.tmbase))
		rec_prev = self.recording

		if not use_autocorrelation:
			if monitor_strength and self.ecount == 0:
				print("%f: signal avg %.1f offavg %.1f" % \
				(self.freq, self.energy_avg, self.energy_off))

			if energy > (self.energy_off + THRESHOLD_SNR):
				self.recording = HISTERESIS

				if rec_prev <= 0:
					print("%s %f: signal %.1f, recording" % \
						(str(datetime.datetime.now()), self.freq, energy))
			else:
				self.recording -= 1
				self.recording = max(0, self.recording)

				if self.recording <= 0 and rec_prev > 0:
					print("%s %f: signal %.1f, stopping" % \
						(str(datetime.datetime.now()), self.freq, energy))
	
			if self.recording <= 0:
				# Use sample to find background noise level
				if energy < self.energy_off:
					self.energy_off = 0.05 * energy + 0.95 * self.energy_off
				else:
					self.energy_off = 0.005 * energy + 0.995 * self.energy_off
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

		if use_autocorrelation:
			# Calculate autocorrelation metric
			ac_r = numpy.abs(numpy.correlate(output_raw, output_raw, 'same'))
			ac_metric = numpy.sum(ac_r) / numpy.max(ac_r) / len(output_raw)

			if self.ac_avg is None:
				self.ac_avg = ac_metric
			else:
				self.ac_avg = 0.1 * ac_metric + 0.9 * self.ac_avg

			if monitor_strength and self.ecount == 0:
				print("%f: signal avg %.1f autocorrelation %f" % \
					(self.freq, self.energy_avg, self.ac_avg))

			if ac_metric > THRESHOLD_AC:
				self.recording = HISTERESIS
				if rec_prev <= 0:
					print("%s %f: autocorrelation %f, recording" % \
						(str(datetime.datetime.now()), self.freq, ac_metric))
			else:
				self.recording -= 1
				self.recording = max(self.recording, 0)

				if self.recording <= 0 and rec_prev > 0:
					print("%s %f: autocorrelation %.1f, stopping" % \
						(str(datetime.datetime.now()), self.freq, ac_metric))

			if self.recording <= 0:
				return

		# Filter to audio bandwidth and decimate
		output_raw = self.audio_filter.feed(output_raw)
		output_raw = self.audio_decimator.feed(output_raw)
		output_raw = numpy.clip(output_raw, -0.999, +0.999)

		# Scale to unsigned 8-bit int with offset (8-bit WAV)
		# output_raw = numpy.clip(output_raw, -0.999, +0.999)
		output_raw = numpy.multiply(output_raw, 127) + 127
		output_raw = output_raw.astype(int)
	
		bits = struct.pack('%dB' % len(output_raw), *output_raw)
		if not self.wav:
			self.create_wav()
		self.wav.writeframes(bits)
		# print("%s %f" % ('f wav', time.time() - self.tmbase))

demodulators = {}
for f in freqs:
	demodulators[f] = Demodulator(f)

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

	# Forward I/Q samples to all channels
	for k, d in demodulators.items():
		d.ingest(iqdata)

for k, d in demodulators.items():
	d.close_queue()

for k, d in demodulators.items():
	d.drain_queue()
