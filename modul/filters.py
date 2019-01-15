#!/usr/bin/env python

import numpy, math
from numpy import fft

SAMPLE_RATE = 44100 # Hz
NYQUIST_RATE = SAMPLE_RATE / 2.0
FFT_LENGTH = 512

def lowpass_coefs(cutoff):
	cutoff /= (NYQUIST_RATE / (FFT_LENGTH / 2.0))

	# create FFT filter mask
	mask = []
	negatives = []
	l = FFT_LENGTH // 2
	for f in range(0, l+1):
		rampdown = 1.0
		if f > cutoff:
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

	b = FFT_LENGTH // 2
	# apply triangular window function
	for n in range(0, b):
    		impulse_response[n] *= (n + 0.0) / b
	for n in range(b + 1, FFT_LENGTH):
    		impulse_response[n] *= (FFT_LENGTH - n + 0.0) / b

	return impulse_response

def lowpass(original, cutoff):
	coefs = lowpass_coefs(cutoff)
	return numpy.convolve(original, coefs)

if __name__ == "__main__":
	import wave, struct
	original = wave.open("NubiaCantaDalva.wav", "r")
	filtered = wave.open("test_fir.wav", "w")
	filtered.setnchannels(1)
	filtered.setsampwidth(2)
	filtered.setframerate(SAMPLE_RATE)

	n = original.getnframes()
	original = struct.unpack('%dh' % n, original.readframes(n))
	original = [s / 2.0**15 for s in original]

	result = lowpass(original, 1000)
	
	result = [ int(sample * 2.0**15) for sample in result ]
	filtered.writeframes(struct.pack('%dh' % len(result), *result))
