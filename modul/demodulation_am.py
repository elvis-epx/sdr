#!/usr/bin/env python

import wave
import struct

modulated = wave.open("am.wav", "r")

f = demod_am = wave.open("demod_am.wav", "w")
f.setnchannels(1)
f.setsampwidth(2)
f.setframerate(44100)

for n in range(0, modulated.getnframes()):
    signal = struct.unpack('h', modulated.readframes(1))[0] / 32768.0
    signal = abs(signal)
    demod_am.writeframes(struct.pack('h', signal * 32767))
