#!/usr/bin/env python

import wave, struct, math
from m3co import *

# This is the message we want to send
msg = open("m3tx.py").read()
# msg = "0123456789 Abracadabra!"

# Convert message to a list of bits, adding start/stop bits
msgbits = []
for byte in msg:
    byte = ord(byte)
    msgbits.append(0) # start bit
    for bit in range(7, -1, -1): # MSB
        msgbits.append((byte >> bit) % 2)
    msgbits.append(1) # stop bit

while len(msgbits) % BITS_PER_SYMBOL:
    msgbits.append(0)

# Randomize
msgbits = [ randomize(bit) for bit in msgbits ]

# Group bit stream into symbols
bitgroups = all_ones[:]
for n in range(0, len(msgbits), BITS_PER_SYMBOL):
    symbol = 0
    for bit in range(0, BITS_PER_SYMBOL):
        symbol += msgbits[n + bit] << (BITS_PER_SYMBOL - bit - 1)
    bitgroups.append(symbol)

# Add 111111s as header and trailer, to help RX serial decoder
bitgroups.extend(all_ones)

qam = wave.open("qam.wav", "w")
qam.setnchannels(1)
qam.setsampwidth(2)
qam.setframerate(SAMPLE_RATE)

t = -1
samples = []

f = CARRIER * math.pi * 2 / SAMPLE_RATE

# Begin with 1 second of pure carrier
for n in range(0, int(SAMPLE_RATE)):
    t += 1
    sample = math.cos(f * t)
    sample *= absolute_modulation_limit
    sample *= avg_power
    samples.append(int(sample * 32767))

qam.writeframes(struct.pack('%dh' % len(samples), *samples))
samples = []

phasor = 0

for symbol in bitgroups:
    point = constellation[symbol]
    x = point.real
    y = point.imag

    # Play the symbol for 1/BAUD_RATE seconds
    for baud_length in range(0, int(SAMPLE_RATE / BAUD_RATE)):
        t += 1
        sample  = x * math.cos(f * t + phasor)
        sample += y * -math.sin(f * t + phasor)
        sample /= max_amplitude_tot
        sample *= absolute_modulation_limit
        samples.append(int(sample * 32767))

    # Sum up phase change so each phase change is "on top" of last symbol
    phasor += cphase(point)
    phasor %= 2 * math.pi

qam.writeframes(struct.pack('%dh' % len(samples), *samples))

print "%d symbols sent" % len(bitgroups)
