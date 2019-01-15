#!/usr/bin/env python

# Coward mode: carrier and amplitude estimation are ideal
coward = False

import wave, struct, math, numpy, random, sys
from m3co import *

qam = wave.open("qam.wav", "r")
n = qam.getnframes()
qam = struct.unpack('%dh' % n, qam.readframes(n))

# Proof that we don't need exact carrier frequency:
# we set a random error.
#
# Phase drift compensation works only if RX carrier is
# *below* TX carrier, so RX must always underestimate
# it, and random range is fully below 1800 Hz.
# Maximum tolerance to carrier deviation
# depends (inversely) on how many bits per symbol
# we are trying to send. Seems to be 15Hz for 16 bits,
# which is very good (real-world modems accept +/- 5Hz).

freq_tolerance = 5 # plus or minus
if not coward:
    CARRIER -= 1.0
    CARRIER -= random.random() * freq_tolerance * 2
    print "Carrier local freq: %.1f" % CARRIER

# Proof that we don't need to know exact carrier phase
ra = random.random() * 2 * math.pi

symbol_length = SAMPLE_RATE / BAUD_RATE

avg_order = int(SAMPLE_RATE)
avg_amplitude = 0.5
avg_memory = [ avg_amplitude for x in range(0, avg_order) ]
avg_weight = 1.0 / avg_order

symbols = []
f = CARRIER * 2 * math.pi / SAMPLE_RATE
carrier_90 = SAMPLE_RATE / CARRIER / 4.0
carrier_90 = int(carrier_90)
phase_drift = 0
phase_drift_tot = 0
phase1 = 0
phase_drift_threshold = 2 * math.pi * (freq_tolerance / CARRIER)
print "Phase drift threshold: %.3f" % (phase_drift_threshold * 180 / math.pi)
pd_weight = 1.0 / 200.0 # takes 200 samples to change it
recovered = []

for t in range(0, len(qam) - carrier_90 - 2):
    sample1 = qam[t+1] / 32768.0
    sample0 = qam[t] / 32768.0
    sample901 = qam[t + carrier_90 + 1] / 32768.0
    sample900 = qam[t + carrier_90] / 32768.0

    if coward:
        scaling = max_amplitude_tot / absolute_modulation_limit
    else:
        scaling = max_amplitude_tot / (avg_amplitude / avg_power)

    # Take derivatives of now and 90 degrees in future
    d_raw = (sample1 - sample0) / f
    d = d_raw * scaling
    d90_raw = (sample901 - sample900) / f
    d90 = d90_raw * scaling

    st = math.sin(f * t + ra)
    ct = math.cos(f * t + ra)

    a = d90 * ct + d * st
    b = d90 * st - d * ct

    # Calculate phase and amplitude
    try:
        tphase = -b / a
        phase = math.atan(tphase)
    except ZeroDivisionError:
        phase = math.pi / 2
        if (-b * a) < 0:
            phase = -phase

    if (abs(d) > abs(d90)):
        amplitude = -d / (st * math.cos(phase) + ct * math.sin(phase))
    else:
        amplitude = -d90 / (-st * math.sin(phase) + ct * math.cos(phase))

    if amplitude < 0:
        amplitude = -amplitude
        phase += math.pi

    phase = main_interval(phase)

    # PLL - phase-locked loop

    # Estimate phase drift due to carrier freq. difference
    phase_diff = main_interval(phase - phase1)

    if abs(phase_diff) < phase_drift_threshold:
        phase_drift = pd_weight * phase_diff + (1.0 - pd_weight) * phase_drift

    phase1 = phase
    phase_drift_tot = main_interval(phase_drift_tot + phase_drift)

    # Remove phase drift from detected signal
    if coward:
        compensated_phase = phase
    else:
        compensated_phase = main_interval(phase - phase_drift_tot)

    # print t,
    # print phase_drift * 180 / math.pi,
    # print compensated_phase * 180 / math.pi,
    # print phase * 180 / math.pi

    if t > SAMPLE_RATE - symbol_length * 2:
        recovered.append(cpx)

    cpx = crect(amplitude, compensated_phase)

    # AGC - Automatic Gain Control

    # Estimate instantaneous amplitude based on raw derivatives
    # Rationale: sin ** 2 + cos ** x = 1, sin' = cos, cos' = -sin

    instant_ampl = math.sqrt(d_raw ** 2 + d90_raw ** 2)

    # Update moving average "memory" and value, rejecting "impossible" levels
    if instant_ampl > 0 and instant_ampl < 1:
        avg_amplitude = avg_amplitude \
                        - avg_weight * avg_memory[0] \
                        + avg_weight * instant_ampl
        del avg_memory[0]
        avg_memory.append(instant_ampl)
    if avg_amplitude < 0.1:
        avg_amplitude = 0.1
    if avg_amplitude >= 1:
        avg_amplitude = 0.999999

    if t > 40000:
        if t % 1000 == 0:
            # print t, avg_amplitude / avg_power * 100
            pass

del qam

settle_time = int(SAMPLE_RATE / BAUD_RATE / 3)
settle_timer = -1
in_symbol = 0
symbols = []
expected_next_symbol = 0
virgin = True

# Detect discrete symbols in continuous waves

last_point = recovered[0]
last_symbol = last_point

for j in recovered:
    expected_next_symbol -= 1
    if in_symbol > 0:
        # we presume we are flying over a valid symbol
        in_symbol -= 1
    elif abs(j - last_point) > (point_radius * 0.5):
        # change detected, look for stabilization in future
        expected_next_symbol = symbol_length
        last_point = j
        settle_timer = settle_time
    elif expected_next_symbol < (-0.15 * symbol_length):
        # should have detected a symbol already
        # assume we have a 0-phase symbol here
        expected_next_symbol += symbol_length
        last_point = j
        settle_timer = settle_time
    elif settle_timer > 0:
        # one sample closer a good symbol
        settle_timer -= 1
    elif settle_timer == 0:
        # signal settled, annotate symbol
        virgin = False
        settle_timer = -1
        in_symbol = int(0.33 * symbol_length)
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

# Derandomize
bits = [ derandomize(bit) for bit in bits ]

# Find bytes based on start and stop bits

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
