#!/usr/bin/env python

import wave
import struct
import math
import random
import time

phase = random.random() * 2 * math.pi

modulated = wave.open("amsc.wav", "r")
demod_amsc_ok = wave.open("demod_amsc_iq.wav", "w")

for f in [demod_amsc_ok]:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)

for n in range(0, modulated.getnframes()):
	signal = struct.unpack('<h', modulated.readframes(1))[0] / 32768.0
	icarrier = math.cos(3000.0 * (n / 44100.0) * math.pi * 2 + phase)
	qcarrier = -math.sin(3000.0 * (n / 44100.0) * math.pi * 2 + phase)
	ibase = signal * icarrier
	qbase = signal * qcarrier
	base = (ibase * ibase + qbase * qbase) ** 0.5
	angle = math.atan2(qbase, ibase)
	if (angle > (+math.pi / 2) and angle < +math.pi) or \
	   (angle < (-math.pi / 2) and angle > -math.pi):
		base = -base
	# print("%f %f" % (base, angle))
	# time.sleep(0.1)

	demod_amsc_ok.writeframes(struct.pack('h', base * 32767))
