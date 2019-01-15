#!/usr/bin/env python

import wave, struct, math

ramp = 0.005
SAMPLE_RATE = 96000
cw_freq = 15000.0

cw1 = wave.open("cw1.wav", "w")
cw1.setnchannels(1)
cw1.setsampwidth(2)
cw1.setframerate(SAMPLE_RATE)

envelope = 0.0

for n in range (0, 2 * SAMPLE_RATE):	
	t = (0.0 + n) / (0.0 + SAMPLE_RATE)
	on = (n % 10000) > 5000
	sample = 0.0
	if on:
		if envelope < 0.8:
			envelope += ramp
	else:
		if envelope > 0.0:
			envelope -= ramp
	sample = envelope * math.cos(2 * math.pi * cw_freq * t)
		
	cw1.writeframes(struct.pack('h', sample * 32767))
