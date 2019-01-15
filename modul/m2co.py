#!/usr/bin/env python

import wave, struct, math

SAMPLE_RATE = 44100.0 # Hz
CARRIER = 1800.0 # Hz
BAUD_RATE = 900.0 # Hz
BITS_PER_SYMBOL = 4 # Bits per symbol

# Current limits (depending on FIR filter calibration)
# 16 bits/symbol at very low rate (WAV limit?)
# 4 bits per symbol @1000Hz
# 6 bits per symbol @900Hz
# ~1000Hz (probably because of FIR filtering of real/imag)

# generate constellation for each possible symbol
COLUMNS = 2 ** int(BITS_PER_SYMBOL / 2)
ROWS = 2 ** (BITS_PER_SYMBOL - int(BITS_PER_SYMBOL / 2))
constellation = {}
invconstellation = {}
max_amplitude_axis = max(ROWS, COLUMNS) - 1.0
max_amplitude_tot = abs(complex(max_amplitude_axis, max_amplitude_axis))
point_diameter = 1.0

for y in range(0, ROWS):
    invconstellation[y] = {}
    for x in range(0, COLUMNS):
        s = y * COLUMNS + x
        point = complex(2 * x - (COLUMNS - 1), 2 * y - (ROWS - 1))
        constellation[s] = point
        invconstellation[point] = s

all_ones = (1 << BITS_PER_SYMBOL) - 1
all_ones = [ all_ones for n in range(0, 30 / BITS_PER_SYMBOL) ]

# FIR lowpass filter for demodulation. Trade-offs:
# 1) Longer filter (big w) is more selective, but increases
# inter-symbol smearing if 2w > symbol length.
# 2) Cutoff frequency: too low and symbols can not be
# distinguished (square wave becomes rounder and rounder);
# too high and 2*carrier noise increases (more noise =
# less bits per symbol).
#
# Clearly some other technique must be employed to RX
# when baud rate ~ carrier frequency!

lowpass = []
CUTOFF = CARRIER
w = int(SAMPLE_RATE / BAUD_RATE / 2)
R = (SAMPLE_RATE / 2.0 / CUTOFF)
for x in range(-w, w+1):
    if x == 0:
       y = 1
    else:
       y = math.sin(x * math.pi / R) / (x * math.pi / R)
       # Hamming window
       n = x + w
       y *= 0.54 - 0.46 * math.cos(2.0 * math.pi * n / (2 * w))
    lowpass.append(y / R)

def cphase(c):
    return math.atan2(c.imag, c.real)

def crect(m, p):
    a = m * math.cos(p)
    b = m * math.sin(p)
    return complex(a, b)

# Return a complex number with same amplitude as 'this', but
# phase equal to angle between 'this' and 'last'

def dphase(this, last):
    diff = cphase(this) - cphase(last)
    return crect(abs(this), diff)

# Round complex number to nearest constellation point

def constellation_round(candidate):
    nearest_distance = 999999.0
    nearest = 0
    for k in constellation.keys():
        point = constellation[k]
        distance = abs(candidate - point)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest = point
    return nearest
