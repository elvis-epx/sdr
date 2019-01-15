#!/usr/bin/env python

import wave, struct, math

ramp = 0.005
SAMPLE_RATE = 96000
bfo_freq_base = 15000.0

cw1 = wave.open("cw1.wav", "r")
cw3 = wave.open("cw3.wav", "w")
cw3.setnchannels(1)
cw3.setsampwidth(2)
cw3.setframerate(SAMPLE_RATE)

for n in range(0, cw1.getnframes()):
	t = (0.0 + n) / (0.0 + SAMPLE_RATE)
	bfo_freq = bfo_freq_base + 0.05 * bfo_freq_base * math.sin(2 * math.pi * t * 0.25)
	cw_sample = struct.unpack('h', cw1.readframes(1))[0] / 32768.0
	bfo = 0.5 * math.cos(2 * math.pi * bfo_freq * t)
	sample = cw_sample * bfo
	cw3.writeframes(struct.pack('h', sample * 32767))
