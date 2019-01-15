#!/usr/bin/env python3

# FM modulator based on I/Q (quadrature) modulation

import wave, struct, math

input_src = wave.open("paralelepipedo_lopass.wav", "r")
FM_CARRIER = 10000.0
MAX_DEVIATION = 1000.0 # Hz

fm = wave.open("iq_fm.wav", "w")
fm.setnchannels(1)
fm.setsampwidth(2)
fm.setframerate(44100)

phase = 0 # in radians
for n in range(0, input_src.getnframes()):
	# rush or drag phase accordingly to input signal
	# this is analog to integrating
	inputsgn = struct.unpack('h', input_src.readframes(1))[0] / 32768.0
	# translate input into a phase change that changes frequency
	# up to MAX_DEVIATION Hz 
	phase += inputsgn * math.pi * MAX_DEVIATION / 44100
	phase %= 2 * math.pi

	# calculate quadrature I/Q
	i = math.cos(phase)
	q = math.sin(phase)

	carrier = 2 * math.pi * FM_CARRIER * (n / 44100.0)
	output = i * math.cos(carrier) - q * math.sin(carrier)

	fm.writeframes(struct.pack('h', int(output * 32767)))
