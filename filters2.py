#!/usr/bin/env python3

import numpy, math, sys, time
from numpy import fft

def impulse(mask):
	# Negative side, a mirror of positive side
	negatives = mask[1:-1]
	negatives.reverse()
	mask = mask + negatives
	fft_length = len(mask)

	# Convert FFT filter mask to FIR coefficients
	impulse_response = fft.ifft(mask).real.tolist()

	# swap left and right sides
	left = impulse_response[:fft_length // 2]
	right = impulse_response[fft_length // 2:]
	impulse_response = right + left

	return impulse_response


def fir_coefs(sample_rate, pass_lo, cutoff_lo, cutoff_hi, pass_hi):
	assert pass_lo is None or cutoff_lo > pass_lo
	assert pass_hi is None or pass_hi > cutoff_hi
	max_freq = sample_rate / 2.0

	if cutoff_lo is not None:
		trans = cutoff_lo - pass_lo
	else:
		trans = 1

	if cutoff_hi is not None:
		trans = min(trans, pass_hi - cutoff_hi)

	bt = max(trans, 1) / sample_rate
	tap_count = 60 # dB attenuation
	tap_count /= 22 * bt
	tap_count = int(tap_count / 2) * 2
	print("Taps: %d" % tap_count, file=sys.stderr)

	f2s = max_freq / (tap_count / 2.0)

	if cutoff_lo is not None:
		cutoff_lo /= f2s
		pass_lo /= f2s
		step_lo = 1.0 / -(pass_lo - cutoff_lo)
		print("lo %f %f %f" % (pass_lo, cutoff_lo, step_lo), file=sys.stderr)

	if cutoff_hi is not None:
		cutoff_hi /= f2s
		pass_hi /= f2s
		step_hi = 1.0 / (pass_hi - cutoff_hi)

	# create FFT filter mask
	l = tap_count // 2
	mask = [ 0 for f in range(0, l+1) ]
	
	if pass_lo is not None:
		# Low-pass filter part
		tap = 0.0
		for f in range(0, l+1):
			if f <= pass_lo:
				tap = 1.0
			elif f > pass_lo and f < cutoff_lo:
				tap -= step_lo # ramp down
			elif f >= cutoff_lo:
				tap = 0.0
			mask[f] = tap

	if pass_hi is not None:
		tap = 0.0
		for f in range(l, -1, -1):
			if f >= pass_hi:
				tap = 1.0
			elif f < pass_hi and f > cutoff_hi:
				tap -= step_hi # ramp down
			elif f <= cutoff_hi:
				tap = 0.0
			mask[f] *= tap

	return impulse(mask)

def deemph_coefs(sample_rate, us, hi, hi_cut):
	max_freq = sample_rate / 2.0

	us /= 1000000
	# us = RC constant of the hypothetical filter
	lo = 1.0 / (2 * math.pi * us)
	assert hi > lo
	assert hi_cut > hi

	trans = min(hi_cut - hi, hi - lo, lo)

	bt = max(trans, 1) / sample_rate
	tap_count = 60 # dB attenuation
	tap_count /= 22 * bt
	tap_count = int(tap_count / 2) * 2
	print("Deemph taps: %d" % tap_count, file=sys.stderr)

	f2s = max_freq / (tap_count / 2.0)
	lo /= f2s
	hi /= f2s
	hi_cut /= f2s
	step_lohi = (10 ** 1) ** (1.0 / (hi - lo)) # 10dB
	step_hicut = (10 ** 5) ** (1.0 / (hi_cut - hi)) # 50dB

	# create FFT filter mask
	l = tap_count // 2
	mask = [ 0 for f in range(0, l+1) ]
	
	tap = 1.0
	for f in range(0, l+1):
		if f <= lo:
			tap = 1
		elif f >= lo and f <= hi:
			tap /= step_lohi
		elif f >= hi and f < hi_cut:
			tap /= step_hicut
		else:
			tap = 0
		mask[f] = tap
	print(mask, file=sys.stderr)

	return impulse(mask)

class filter:
	def __init__(self, sample_rate, cutoff):
		raise "Abstract"

	def feed(self, original):
		unfiltered = numpy.concatenate((self.buf, original))
		self.buf = unfiltered[-len(self.coefs):]
		filtered = numpy.convolve(unfiltered, self.coefs, mode='valid')
		assert len(filtered) == len(original) + 1
		return filtered[1:]

class lowpass(filter):
	def __init__(self, sample_rate, f, cut):
		self.coefs = fir_coefs(sample_rate, f, cut, None, None)
		self.buf = [ 0 for n in self.coefs ]

class highpass(filter):
	def __init__(self, sample_rate, cut, f):
		self.coefs = fir_coefs(sample_rate, None, None, cut, f)
		self.buf = [ 0 for n in self.coefs ]

class bandpass(filter):
	def __init__(self, sample_rate, cut_f1, f1, f2, cut_f2):
		self.coefs = fir_coefs(sample_rate, f2, cut_f2, cut_f1, f1)
		self.buf = [ 0 for n in self.coefs ]

class deemph(filter):
	def __init__(self, sample_rate, us, hi, hi_cut):
		self.coefs = deemph_coefs(sample_rate, us, hi, hi_cut)
		self.buf = [ 0 for n in self.coefs ]

class decimator(filter):
	def __init__(self, factor):
		self.buf2 = []
		self.factor = int(factor)

	def feed(self, original):
		original = numpy.concatenate((self.buf2, original))

		# Gets the last n-th sample of every n (n = factor)
		# If e.g. gets 12 samples, gets s[4] and s[9], and
		# stoves s[10:] to the next round
		decimated = [ original[ self.factor * i + self.factor - 1 ] \
			for i in range(0, len(original) // self.factor) ]
		self.buf2 = original[:-len(original) % self.factor]

		return decimated
