#!/usr/bin/env python

# v4:
# Rounder constellation
# convolution code
# synchronous

import wave, struct, math, sys, random
from gray import gray

CARRIER = 1800.0 # Hz
SAMPLE_RATE = 43200.0 # Hz
BAUD_RATE = 2400.0 # Hz
BITS_PER_SYMBOL = 8 # Bits per symbol
absolute_modulation_limit = 0.9

# Use even bits per symbol, because it has more optimal
# constellation distribution. Odd bits doesn't work well
# above 7 bits/symbol, while even bits go up to 16.

# generate constellation for each possible symbol
COLUMNS = 2 ** int(BITS_PER_SYMBOL / 2)
ROWS = 2 ** (BITS_PER_SYMBOL - int(BITS_PER_SYMBOL / 2))
constellation = {}
constellation_a = {}
constellation_b = {}
invconstellation = {}
max_amplitude_axis = max(ROWS - 1, COLUMNS - 1)
max_amplitude_tot = abs(complex(max_amplitude_axis, max_amplitude_axis))
point_radius = 1.0
avg_power = 0.0

for y in range(0, ROWS):
    b = 2 * y - (ROWS - 1)
    for x in range(0, COLUMNS):
        s = gray(y * COLUMNS + x)
        a = 2 * x - (COLUMNS - 1)
        point = complex(a, b)
        constellation[s] = point
        constellation_a[a] = None
        constellation_b[b] = None
        invconstellation[point] = s
        avg_power += abs(point)

all_ones = (1 << BITS_PER_SYMBOL) - 1
all_ones = [ all_ones for n in range(0, 30 / BITS_PER_SYMBOL) ]

avg_power /= len(constellation.keys())
avg_power /= max_amplitude_tot
print "Average power per symbol: %.3f" % avg_power

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
# WARNING: takes advantage on fact that constellation is
# rectangular.

def nearest(haystack, needle):
    nearest_distance = 999999999.0
    nearest_value = 0
    for k in haystack.keys():
        distance = abs(k - needle)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_value = k
    return nearest_value

def constellation_round(candidate):
    a = nearest(constellation_a, candidate.real)
    b = nearest(constellation_b, candidate.imag)
    return complex(a, b)

# Makes sure phase is in interval (0, 2 pi)

def main_interval(phase):
    while phase < 0.0:
        phase += math.pi * 2
    phase %= math.pi * 2
    if phase > (math.pi * 2 - 0.00000001):
        phase = 0.0
    return phase

# Randomizer: 1 + x**-3 + x **-4

def randomize(b0):
    global b1, b2, b3, b4
    bs = b0 ^ (b3 ^ b4)
    b1, b2, b3, b4 = bs, b1, b2, b3
    return bs

def derandomize(b0):
    global b1, b2, b3, b4
    bt = b0 ^ (b3 ^ b4)
    b1, b2, b3, b4 = b0, b1, b2, b3
    return bt

rseq = [ int(random.random() * 2) for x in range(0, 25) ]
b1, b2, b3, b4 = (0, 0, 0, 0)
rseqS = [ randomize(b) for b in rseq ]
b1, b2, b3, b4 = (0, 0, 0, 0)
rseqT = [ derandomize(b) for b in rseqS ]
b1, b2, b3, b4 = (0, 0, 0, 0)

if rseqT != rseq:
    print "Randomizer is broken"
    print rseq
    print rseqS
    print rseqT
    sys.exit(1)

