#!/usr/bin/env python3

import numpy, math
from numpy import fft

def fir_coefs(sample_rate, pass_lo, cutoff_lo, cutoff_hi, pass_hi):
	assert cutoff_lo > pass_lo
	assert pass_hi > cutoff_hi
	nyquist_rate = sample_rate / 2.0
	fft_length = 1024
	f2s = nyquist_rate / (fft_length / 2.0)

	cutoff_lo /= f2s
	pass_lo /= f2s
	cutoff_lo /= f2s
	pass_lo /= f2s

	step_lo = 1.0 / abs(pass_lo / cutoff_lo)
	step_hi = 1.0 / abs(pass_hi / cutoff_hi)

	# create FFT filter mask
	l = fft_length // 2
	mask = [ 0 for f in range(0, l+1) ]
	
	# Low-pass filter part
	tap = 0.0
	for f in range(0, l+1):
		if f <= pass_lo:
			tap = 1.0
		elif f > pass_lo:
			tap -= step_lo # ramp down
		elif f > cutoff_lo:
			tap = 0.0
		mask[f] = tap

	tap = 0.0
	for f in range(l, -1, -1):
		if f >= pass_hi:
			tap = 1.0
		elif f < pass_hi:
			tap -= step_hi # ramp down
		elif f < cutoff_hi:
			tap = 0.0
		mask[f] = min(1.0, max(-1.0, mask[f] + tap ))

	# Negative side, a mirror of positive side
	negatives = mask[1:-1]
	negatives.reverse()
	mask = mask + negatives

	# Convert FFT filter mask to FIR coefficients
	impulse_response = fft.ifft(mask).real.tolist()

	# swap left and right sides
	left = impulse_response[:fft_length // 2]
	right = impulse_response[fft_length // 2:]
	impulse_response = right + left

	return impulse_response

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
		self.coefs = fir_coefs(sample_rate, f, cut, -2, -1)
		self.buf = [ 0 for n in self.coefs ]


class highpass(filter):
	def __init__(self, sample_rate, cut, f):
		self.coefs = fir_coefs(sample_rate, 1e100, 1e101, cut, f)
		self.buf = [ 0 for n in self.coefs ]

class bandpass(filter):
	def __init__(self, sample_rate, cut_f1, f1, f2, cut_f2):
		self.coefs = fir_coefs(sample_rate, f2, cut_f2, cut_f1, f1)
		self.buf = [ 0 for n in self.coefs ]
