#!/usr/bin/env python3

import numpy, math, sys, time
from numpy import fft

def impulse(mask):
	''' Convert frequency domain mask to time-domain '''
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


def lo_mask(sample_rate, tap_count, freq, dboct):
	''' Create a freq domain mask for a lowpass filter '''
	order = dboct / 6
	max_freq = sample_rate / 2.0
	f2s = max_freq / (tap_count / 2.0)
	# Convert freq to filter step unit
	freq /= f2s
	l = tap_count // 2
	mask = []
	for f in range(0, l+1):
		H = 1.0 / ( 1 + (f / freq) ** (2 * order) ) ** 0.5
		mask.append(H)
	return mask


def hi_mask(sample_rate, tap_count, freq, dboct):
	''' Create a freq domain mask for a highpass filter '''
	order = dboct / 6
	max_freq = sample_rate / 2.0
	f2s = max_freq / (tap_count / 2.0)
	# Convert freq frequency to filter step unit
	freq /= f2s
	l = tap_count // 2
	mask = []
	for f in range(0, l+1):
		H = 1.0 / ( 1 + (freq / (f + 0.0001)) ** (2 * order) ) ** 0.5
		mask.append(H)
	return mask


def combine_masks(mask1, mask2):
	''' Combine two filter masks '''
	assert len(mask1) == len(mask2)
	return [ mask1[i] * mask2[i] for i in range(0, len(mask1)) ]


def taps(sample_rate, freq, dboct, is_highpass):
	cutoff_octaves = 60 / dboct

	if is_highpass:
		cutoff = freq / 2 ** cutoff_octaves
	else:
		cutoff = freq * 2 ** cutoff_octaves
		cutoff = min(cutoff, sample_rate / 2)

	transition_band = abs(freq - cutoff)
	Bt = transition_band / sample_rate
	taps = int(60 / (22 * Bt))
	print("Freq=%f,%f number of taps: %d" % (freq, cutoff, taps), file=sys.stderr)
	return taps


class filter:
	def __init__(self, sample_rate, cutoff):
		raise "Abstract"

	def feed(self, original):
		unfiltered = numpy.concatenate((self.buf, original))
		self.buf = unfiltered[-len(self.coefs):]
		filtered = numpy.convolve(unfiltered, self.coefs, mode='valid')
		assert len(filtered) == len(original) + 1
		return filtered[1:]


class low_pass(filter):
	def __init__(self, sample_rate, f, dbo):
		tap_count = taps(sample_rate, f, dbo, False)
		mask = lo_mask(sample_rate, tap_count, f, dbo)
		self.coefs = impulse(mask)
		self.buf = [ 0 for n in self.coefs ]


class high_pass(filter):
	def __init__(self, sample_rate, f, dbo):
		tap_count = taps(sample_rate, f, dbo, True)
		mask = hi_mask(sample_rate, tap_count, f, dbo)
		self.coefs = impulse(mask)
		self.buf = [ 0 for n in self.coefs ]


class band_pass(filter):
	def __init__(self, sample_rate, lo, hi, dbo):
		tap_count = max(taps(sample_rate, lo, dbo, True),
				taps(sample_rate, hi, dbo, False))
		lomask = lo_mask(sample_rate, tap_count, hi, dbo)
		himask = hi_mask(sample_rate, tap_count, lo, dbo)
		mask = combine_masks(lomask, himask)
		self.coefs = impulse(mask)
		self.buf = [ 0 for n in self.coefs ]


class deemphasis(filter):
	def __init__(self, sample_rate, us, hi, final_dbo):
		# us = RC constant of the hypothetical deemphasis filter
		us /= 1000000
		# 0..lo is not deemphasized
		lo = 1.0 / (2 * math.pi * us)
		# attenuation from lo to hi should be 10dB
		octaves = math.log(hi / lo) / math.log(2)
		# slope in dB/octave of deemphasis filter
		dedbo = 10 / octaves

		tap_count = max(taps(sample_rate, lo, dedbo, False),
				taps(sample_rate, hi, final_dbo, False))

		# Calculate deemphasis filter
		demask = lo_mask(sample_rate, tap_count, lo, dedbo)
		# Calculate low-pass filter after deemphasis
		fmask = lo_mask(sample_rate, tap_count, hi, final_dbo)

		mask = combine_masks(demask, fmask)
		self.coefs = impulse(mask)
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
