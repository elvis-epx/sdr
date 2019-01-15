#!/usr/bin/env python

import wave, struct, math

baseband = wave.open("paralelepipedo_lopass.wav", "r")

amsc = wave.open("amsc.wav", "w")
am = wave.open("am.wav", "w")
carrier = wave.open("carrier3000.wav", "w")

for f in [am, amsc, carrier]:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)

for n in range(0, baseband.getnframes()):
    base = struct.unpack('h', baseband.readframes(1))[0] / 32768.0
    carrier_sample = math.cos(3000.0 * (n / 44100.0) * math.pi * 2)

    signal_am = signal_amsc = base * carrier_sample
    signal_am += carrier_sample
    signal_am /= 2

    amsc.writeframes(struct.pack('h', signal_amsc * 32767))
    am.writeframes(struct.pack('h', signal_am * 32767))
    carrier.writeframes(struct.pack('h', carrier_sample * 32767))
