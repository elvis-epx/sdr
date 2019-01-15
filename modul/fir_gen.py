#!/usr/bin/env python

LOWPASS = 40000.0 # Hz
HIGHPASS = 2000.0 # Hz
SAMPLE_RATE = 44100 # Hz

import wave, struct, math
from numpy import fft
FFT_LENGTH = 512

NYQUIST_RATE = SAMPLE_RATE / 2.0
LOWPASS /= (NYQUIST_RATE / (FFT_LENGTH / 2.0))
HIGHPASS /= (NYQUIST_RATE / (FFT_LENGTH / 2.0))

# Builds filter mask. Note that this sharp-cut filter is BAD
mask = []
negatives = []
l = FFT_LENGTH / 2
for f in range(0, l+1):
    rampdown = 1.0
    if f > LOWPASS:
        rampdown = 0
    if f < HIGHPASS:
        rampdown = 0
    mask.append(rampdown)
    if f > 0 and f < l:
        negatives.append(rampdown)

negatives.reverse()
mask = mask + negatives

fir = wave.open("fir_filter.wav", "w")
fir.setnchannels(1)
fir.setsampwidth(4)
fir.setframerate(SAMPLE_RATE)

# Convert filter from frequency domain to time domain
impulse_response = fft.ifft(mask).real.tolist()

# swap left and right sides
left = impulse_response[:FFT_LENGTH / 2]
right = impulse_response[FFT_LENGTH / 2:]
impulse_response = right + left

b = FFT_LENGTH / 2
# apply triangular window function
for n in range(0, b):
    impulse_response[n] *= (n + 0.0) / b
for n in range(b + 1, FFT_LENGTH):
    impulse_response[n] *= (FFT_LENGTH - n + 0.0) / b

# write in a normal WAV file
impulse_response = [ sample * 2**31 for sample in impulse_response ]
fir.writeframes(struct.pack('%di' % len(impulse_response),
                                 *impulse_response))
