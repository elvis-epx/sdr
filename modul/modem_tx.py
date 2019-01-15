#!/usr/bin/env python

import wave, struct, math

SAMPLE_RATE = 44100.0 # Hz
CARRIER = 1800.0 # Hz
BAUD_RATE = 360.0 # Hz
PHASES = 8
AMPLITUDES = 4
BITS_PER_SYMBOL = 5

# generate constellation of phases and amplitudes
# for each possible symbol, and attribute it to a
# certain bit pattern. I avoided deliberately the
# complex numbers, even though they make things
# easier when dealing with constellations.
#
# Make sure that all ones = maximum aplitude and 0 phase
constellation = {}
for p in range(0, PHASES):
    for a in range(0, AMPLITUDES):
        s = p * AMPLITUDES + a
        constellation[s] = (PHASES - p - 1, a + 1)

# This is the message we want to send
msg = "Abracadabra!"
# msg = open("modem_tx.py").read()

# Convert message to a list of bits, adding start/stop bits
msgbits = []
for byte in msg:
    byte = ord(byte)
    msgbits.append(0) # start bit
    for bit in range(7, -1, -1): # MSB
        msgbits.append((byte >> bit) % 2)
    msgbits.append(1) # stop bit

# Round bit stream to BITS_PER_SYMBOL
while len(msgbits) % BITS_PER_SYMBOL:
    msgbits.append(0)

# Group bit stream into symbols
msgsymbols = []
for n in range(0, len(msgbits), BITS_PER_SYMBOL):
    symbol = 0
    for bit in range(0, BITS_PER_SYMBOL):
        symbol += msgbits[n + bit] << (BITS_PER_SYMBOL - bit - 1)
    msgsymbols.append(symbol)

# Add 1 second worth of all-1 bits in header, plus a trailer.
# The 11111 bit pattern generates a pure carrier, that receiver
# can recognize and train.
allones = (1 << BITS_PER_SYMBOL) - 1
train_sequence = [ allones for x in range(0, int(BAUD_RATE)) ]
finish_sequence = [ allones, allones ]
msgsymbols = train_sequence + msgsymbols + finish_sequence

qam = wave.open("qam.wav", "w")
qam.setnchannels(1)
qam.setsampwidth(2)
qam.setframerate(44100)

t = -1
phase_int = 0
samples = []
for symbol in msgsymbols:
    amplitude = 0.9 * constellation[symbol][1] / AMPLITUDES
    # Phase change is integrated so we don't need absolute phase
    # at receiver side.
    phase_int += constellation[symbol][0]
    phase_int %= PHASES
    phase = phase_int / (0.0 + PHASES)

    # It would be easier to manipulate phase using complex numbers,
    # but I thought this way would be clearer.

    # Play the carrier at chosen phase/amplitude for 1/BAUD_RATE seconds
    for baud_length in range(0, int(SAMPLE_RATE / BAUD_RATE)):
        t += 1
        sample = math.cos(CARRIER * t * math.pi * 2 / SAMPLE_RATE \
                          + 2 * math.pi * phase)
        sample *= amplitude
        samples.append(int(sample * 32767))

qam.writeframes(struct.pack('%dh' % len(samples), *samples))

print "%d symbols sent" % len(msgsymbols)

