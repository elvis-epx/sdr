#!/usr/bin/env python

import wave, struct, math

ramp = 0.005
SAMPLE_RATE = 96000
bfo_freq = 15800.0

cw1 = wave.open("cw1.wav", "r")
cw2 = wave.open("cw2.wav", "w")
cw2.setnchannels(1)
cw2.setsampwidth(2)
cw2.setframerate(SAMPLE_RATE)

for n in range(0, cw1.getnframes()):	
	t = (0.0 + n) / (0.0 + SAMPLE_RATE)
	cw_sample = struct.unpack('h', cw1.readframes(1))[0] / 32768.0
	bfo = 0.5 * math.cos(2 * math.pi * bfo_freq * t)
	sample = cw_sample * bfo
	cw2.writeframes(struct.pack('h', sample * 32767))
