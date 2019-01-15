#!/usr/bin/env python3

import numpy, math
from numpy import fft

def fir_coefs(SAMPLE_RATE, cutoff_min, cutoff_max):
	NYQUIST_RATE = SAMPLE_RATE / 2.0
	FFT_LENGTH = 512
	cutoff_min /= (NYQUIST_RATE / (FFT_LENGTH / 2.0))
	cutoff_max /= (NYQUIST_RATE / (FFT_LENGTH / 2.0))

	# create FFT filter mask
	mask = []
	negatives = []
	l = FFT_LENGTH // 2
	for f in range(0, l+1):
		rampdown = 1.0
		if f > cutoff_max or f < cutoff_min:
			rampdown = 0
		mask.append(rampdown)
		if f > 0 and f < l:
			negatives.append(rampdown)

	negatives.reverse()
	mask = mask + negatives

	# Convert FFT filter mask to FIR coefficients
	impulse_response = fft.ifft(mask).real.tolist()

	# swap left and right sides
	left = impulse_response[:FFT_LENGTH // 2]
	right = impulse_response[FFT_LENGTH // 2:]
	impulse_response = right + left

	# b = FFT_LENGTH // 2
	# apply triangular window function
	# for n in range(0, b):
    	#	impulse_response[n] *= (n + 0.0) / b
	# for n in range(b + 1, FFT_LENGTH):
    	#	impulse_response[n] *= (FFT_LENGTH - n + 0.0) / b

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
	def __init__(self, sample_rate, cutoff):
		self.coefs = fir_coefs(sample_rate, 0, cutoff)
		self.buf = [ 0 for n in self.coefs ]


class highpass(filter):
	def __init__(self, sample_rate, cutoff):
		self.coefs = fir_coefs(sample_rate, cutoff, 99999999999)
		self.buf = [ 0 for n in self.coefs ]

class bandpass(filter):
	def __init__(self, sample_rate, cutoff1, cutoff2):
		self.coefs = fir_coefs(sample_rate, cutoff1, cutoff2)
		self.buf = [ 0 for n in self.coefs ]
