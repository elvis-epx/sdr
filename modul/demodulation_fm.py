#!/usr/bin/env python

SAMPLE_RATE = 44100 # Hz
FM_BAND = 1000.0
FM_CARRIER = 44100 / 8.0
LOWPASS = FM_CARRIER - FM_BAND
HIGHPASS = FM_CARRIER + FM_BAND
HIGHPASS2 = FM_BAND # Hz

import wave, struct, math
from numpy import fft
FFT_LENGTH = 2048
OVERLAP = 512
FFT_SAMPLE = FFT_LENGTH - OVERLAP
NYQUIST_RATE = SAMPLE_RATE / 2.0

LOWPASS /= (NYQUIST_RATE / (FFT_LENGTH / 2.0))
HIGHPASS /= (NYQUIST_RATE / (FFT_LENGTH / 2.0))
HIGHPASS2 /= (NYQUIST_RATE / (FFT_LENGTH / 2.0))

zeros = [ 0 for x in range(0, OVERLAP) ]

mask = []
for f in range(0, FFT_LENGTH / 2 + 1):
    if f < LOWPASS or f > HIGHPASS:
        ramp = 0.0
    else:
        ramp = (f - LOWPASS) / (HIGHPASS - LOWPASS)
    mask.append(ramp)

mask2 = []
for f in range(0, FFT_LENGTH / 2 + 1):
    if f > HIGHPASS2 or f == 0:
        ramp = 0.0
    else:
        ramp = 1.0
    mask2.append(ramp)

fm = wave.open("fm.wav", "r")
demodulated = wave.open("demod_fm.wav", "w")
demodulated.setnchannels(1)
demodulated.setsampwidth(2)
demodulated.setframerate(SAMPLE_RATE)

n = fm.getnframes()
fm = struct.unpack('%dh' % n, fm.readframes(n))
# scale from 16-bit signed WAV to float
fm = [s / 32768.0 for s in fm]

saved_td = zeros
intermediate = []

for pos in range(0, len(fm), FFT_SAMPLE):
    time_sample = fm[pos : pos + FFT_LENGTH]

    frequency_domain = fft.fft(time_sample, FFT_LENGTH)
    l = len(frequency_domain)

    for f in range(0, l/2+1):
        frequency_domain[f] *= mask[f]

    for f in range(l-1, l/2, -1):
        cf = l - f
        frequency_domain[f] *= mask[cf]

    time_domain = fft.ifft(frequency_domain)

    for i in range(0, OVERLAP):
        time_domain[i] *= (i + 0.0) / OVERLAP
        time_domain[i] += saved_td[i] * (1.0 - (i + 0.00) / OVERLAP)

    saved_td = time_domain[FFT_SAMPLE:]
    time_domain = time_domain[:FFT_SAMPLE]

    intermediate += time_domain.real.tolist()

intermediate = [ abs(sample) for sample in intermediate ]

saved_td = zeros
output = []

del fm

for pos in range(0, len(intermediate), FFT_SAMPLE):
    time_sample = intermediate[pos : pos + FFT_LENGTH]

    frequency_domain = fft.fft(time_sample, FFT_LENGTH)
    l = len(frequency_domain)

    for f in range(0, l/2+1):
        frequency_domain[f] *= mask2[f]

    for f in range(l-1, l/2, -1):
        cf = l - f
        frequency_domain[f] *= mask2[cf]

    time_domain = fft.ifft(frequency_domain)

    for i in range(0, OVERLAP):
        time_domain[i] *= (i + 0.0) / OVERLAP
        time_domain[i] += saved_td[i] * (1.0 - (i + 0.00) / OVERLAP)

    saved_td = time_domain[FFT_SAMPLE:]
    time_domain = time_domain[:FFT_SAMPLE]

    output += time_domain.real.tolist()

output = [ int(sample * 32767) for sample in output ]

demodulated.writeframes(struct.pack('%dh' % len(output), *output))
