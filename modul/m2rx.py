#!/usr/bin/env python

import wave, struct, math, numpy, random
from m2co import *

qam = wave.open("qam.wav", "r")
n = qam.getnframes()
qam = struct.unpack('%dh' % n, qam.readframes(n))
qam = [ sample / 32768.0 for sample in qam ]

recovered = []

t = int(random.random() * CARRIER)

for sample in qam:
    t += 1
    angle = CARRIER * t * 2 * math.pi / SAMPLE_RATE
    a = sample * math.cos(angle)
    b = sample * -math.sin(angle)
    recovered.append(complex(a, b))

del qam

# Pass signal through lowpass filter
recovered = numpy.convolve(recovered, lowpass)

f = wave.open("mreal.wav", "w")
f.setnchannels(1)
f.setsampwidth(2)
f.setframerate(44100)
bla = [ int(sample.real * 32767) for sample in recovered ]
f.writeframes(struct.pack('%dh' % len(bla), *bla))

f = wave.open("mimag.wav", "w")
f.setnchannels(1)
f.setsampwidth(2)
f.setframerate(44100)
bla = [ int(sample.imag * 32767) for sample in recovered ]
f.writeframes(struct.pack('%dh' % len(bla), *bla))

# Find maximum amplitude based on training whistle (1s)

energy = 0.0
for t in range(int(0.1 * SAMPLE_RATE), int(0.9 * SAMPLE_RATE)):
    energy += recovered[t]

energy /= int(0.8 * SAMPLE_RATE)
max_rx_amplitude = abs(energy)

# skew = cphase(energy)
# print "Max RX amplitude: ", max_rx_amplitude
# print "Carrier phase difference: %d degrees" % (skew * 180 / math.pi)

# Scale values to constellation amplitudes

scale = max_amplitude_tot / max_rx_amplitude
recovered = [ sample * scale for sample in recovered ]

settle_time = int(SAMPLE_RATE / BAUD_RATE / 8)
settle_timer = -1
in_symbol = 0
symbols = []
expected_next_symbol = SAMPLE_RATE / BAUD_RATE
lost = 0

# Detect discrete symbols in continuous waves
# Relies on fact that every symbol in constellation changes phase!

begin = int(0.9 * SAMPLE_RATE)
last_point = recovered[begin]
last_symbol = last_point

for j in recovered[begin+1:]:
    if in_symbol > 0:
        # we presume we are flying over a valid symbol
        in_symbol -= 1
    elif abs(j - last_point) > (point_diameter * 0.5):
        # change detected, look for stabilization in future
        last_point = j
        settle_timer = settle_time
    elif settle_timer > 0:
        # one sample closer a good symbol
        settle_timer -= 1
    elif settle_timer == 0:
        # signal settled, annotate symbol
        settle_timer = -1
        in_symbol = int(0.85 * SAMPLE_RATE / BAUD_RATE)
        # Take phase difference between present and last symbols
        rj = dphase(j, last_symbol)
        # print rj, j
        symbols.append(rj)
        last_point = j
        last_symbol = j

del recovered

print "%d symbols found" % len(symbols)

# Translate constellation points into bit sequences

bitgroups = []
for symbol in symbols:
    symbol = constellation_round(symbol)
    try:
        bitgroups.append(invconstellation[symbol])
    except KeyError:
        # print "Bad symbol:", symbol, ", ignored"
        pass

# Translate bit groups into individual bits

bits = []
for bitgroup in bitgroups:
    for bit in range(0, BITS_PER_SYMBOL):
        bits.append((bitgroup >> (BITS_PER_SYMBOL - bit - 1)) % 2)

# Find bytes based on start and stop bits. This will make you feel
# like a poor RS-232 port :)

t = 0
state = 0
byte = []
bytes = []
while t < len(bits):
    bit = bits[t]
    if state == 0:
        # did not find start bit
        if not bit:
            # just found start bit
            state = 1
    elif state == 1:
        # found start bit, accumulating a byte
        if len(byte) < 8:
            byte.append(bit)
        else:
            # byte complete, test stop bit
            if bit:
                # stop bit is there
                bytes.append(byte)
            else:
                # oops, stop bit not there, we were cheated!
                # backtrack to the point fake start bit was 'found'
                t -= 8
            byte = []
            state = 0
    t += 1


# Make a string from the bytes

msg = ""
# print "Bytes:",
for byte in bytes:
    value = 0
    for bit in range(0, 8):
        value += byte[bit] << (8 - bit - 1)
    msg += chr(value)
    # print value,

print msg
