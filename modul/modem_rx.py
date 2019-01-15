#!/usr/bin/env python

import wave, struct, math, numpy, random

SAMPLE_RATE = 44100.0 # Hz
CARRIER = 1800.0 # Hz
BAUD_RATE = 360.0 # Hz
PHASES = 8
AMPLITUDES = 4
BITS_PER_SYMBOL = 5

# FIR lowpass filter. This time we calculated the coefficients
# directly, without resorting to FFT.
lowpass = []
CUTOFF = BAUD_RATE * 4
w = int(SAMPLE_RATE / CUTOFF)
R = (SAMPLE_RATE / 2.0 / CUTOFF)
for x in range(-w, w):
    if x == 0:
       y = 1
    else:
       y = math.sin(x * math.pi / R) / (x * math.pi / R)
    lowpass.append(y / R)

# Modem constellation (the same as TX side)
constellation = {}
invconstellation = {}
for p in range(0, PHASES):
    invconstellation[PHASES - p - 1] = {}
    for a in range(0, AMPLITUDES):
        s = p * AMPLITUDES + a
        constellation[s] = (PHASES - p - 1, a + 1)
        invconstellation[PHASES - p - 1][a + 1] = s

qam = wave.open("qam.wav", "r")
n = qam.getnframes()
qam = struct.unpack('%dh' % n, qam.readframes(n))
qam = [ sample / 32768.0 for sample in qam ]

# Demodulate in "real" and "imaginary" parts. The "real" part
# is the correlation with carrier. The "imaginary" part is the
# correlation with carrier offset 90 degrees. Having both values
# allows us to find QAM signal's phase.

real = []
imag = []
amplitude = []

# This proofs that we don't need to replicate the original carrier
# (at least, not in the same phase). Sometimes this random carrier
# phase makes the receiver to interpret training sequence as a 
# character, but nothing serious.

t = int(random.random() * CARRIER)
# t = -1

# In the other hand, frequency must match carrier exactly; if we
# need to allow for frequency deviations, we must build a digital
# equivalent to PLL / VCO oscilator.

for sample in qam:
    t += 1
    angle = CARRIER * t * 2 * math.pi / SAMPLE_RATE
    real.append(sample * math.cos(angle))
    imag.append(sample * -math.sin(angle))
    amplitude.append(abs(sample))

del qam

# Pass all signals through lowpass filter
real = numpy.convolve(real, lowpass)
imag = numpy.convolve(imag, lowpass)
amplitude = numpy.convolve(amplitude, lowpass)

# After lowpass filter, all three lists show something like
# a square wave, pretty much like the original bitstream.
# If you want to see the result of early detection phase,
# uncomment this:

# f = wave.open("teste.wav", "w")
# f.setnchannels(1)
# f.setsampwidth(2)
# f.setframerate(44100)
# bla = [ int(sample * 32767) for sample in imag ]
# f.writeframes(struct.pack('%dh' % len(bla), *bla))

# Detect phase based on real and imaginary values

phase = []
wrap = 2.0 * math.pi * (PHASES - 0.5) / PHASES
for t in range(0, len(real)):
    # This converts (real, imag) to an angle
    angle = math.atan2(imag[t], real[t])
    if angle < 0:
        angle += 2 * math.pi
    # Move angle near to 2 pi to 0
    if angle > wrap:
        angle = 0.0
    phase.append(angle)

# Find maximum amplitude based on training whistle (1s), and
# measure how much our local carrier is out-of-phase in
# relationship to QAM signal

max_amplitude = 0.0
carrier_real = 0.0
carrier_imag = 0.0
for t in range(int(0.1 * SAMPLE_RATE), int(0.9 * SAMPLE_RATE)):
    max_amplitude += amplitude[t]
    carrier_real += real[t]
    carrier_imag += imag[t]

max_amplitude /= int(0.8 * SAMPLE_RATE)
carrier_real /= int(0.8 * SAMPLE_RATE)
carrier_imag /= int(0.8 * SAMPLE_RATE)

skew = math.atan2(carrier_imag, carrier_real)

print "Carrier phase difference: %d degrees" % (skew * 180 / math.pi)

del imag
del real

# Normalize/quantify amplitude and phase to constellation steps
qsymbols = []
for t in range(0, len(phase)):
    p = phase[t]
    a = amplitude[t]
    a /= max_amplitude
    a = int(a * AMPLITUDES + 0.49)

    # Compensate for local carrier phase difference
    # This ensures the best phase quantization (avoiding that
    # quantization edge is too near a constellation point)

    p += 2 * math.pi - skew
    p /= 2 * math.pi
    p = int(p * PHASES + 0.49) % PHASES

    qsymbols.append((p, a))

del phase
del amplitude

# Try to detect edges between symbols

edge = []
settle_time = int(SAMPLE_RATE / BAUD_RATE / 8)
settle_timer = -1
in_symbol = 0
first_symbol = 0
last_a = last_p = 0
for t in range(0, len(qsymbols)):
    s = 0
    p, a = qsymbols[t]
    if in_symbol > 0:
        # we presume we are flying over a valid symbol
        in_symbol -= 1
    elif a != last_a or p != last_p:
        # change detected, look for stabilization in future
        settle_timer = settle_time
    elif settle_timer > 0:
        # one sample closer a good symbol
        settle_timer -= 1
    elif settle_timer == 0:
        # signal settled for (settle_time) samples;
        # take the current signal as a valid symbol
        settle_timer = -1
        in_symbol = int(0.85 * SAMPLE_RATE / BAUD_RATE)
        if t > 0.5 * SAMPLE_RATE:
            # make sure we are not at the beginning
            s = 1
            if not first_symbol:
                first_symbol = t
    edge.append(s)
    last_p = p
    last_a = a

# Find symbols based on edges and known baud rate

symbols = []
expected_next_symbol = SAMPLE_RATE / BAUD_RATE
lost = 0

for t in range(first_symbol - int(SAMPLE_RATE * 0.1), len(qsymbols)):
    p, a = qsymbols[t]
    s = edge[t]

    if s:
        # amplitude/phase edge, strong hint for symbol
        lost = 0
        symbols.append([p, a])
    else:
        lost += 1

    if lost > expected_next_symbol * 1.5:
        # no edge yet, take this as a non-transition signal
        lost -= expected_next_symbol
        symbols.append([p, a])

del qsymbols
del edge

print "%d symbols found" % len(symbols)

# Differentiate phase (because we had integrated it at transmitter)

last_phase = 0
for t in range(0, len(symbols)):
    p = symbols[t][0]
    symbols[t][0] = (p - last_phase + PHASES) % PHASES
    last_phase = p

# Translate constellation points into bit sequences

bitgroups = []
for t in range(0, len(symbols)):
    p, a = symbols[t]
    try:
        bitgroups.append(invconstellation[p][a])
    except KeyError:
        print "Bad symbol:", p, a, ", ignored"

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
print "Bytes:",
for byte in bytes:
    value = 0
    for bit in range(0, 8):
        value += byte[bit] << (8 - bit - 1)
    msg += chr(value)
    print value,

print
print msg
