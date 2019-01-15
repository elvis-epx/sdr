#!/usr/bin/env python

import wave
import struct
import math

modulated = wave.open("amsc.wav", "r")

demod_amsc_ok = wave.open("demod_amsc_ok.wav", "w")
demod_amsc_nok = wave.open("demod_amsc_nok.wav", "w")
demod_amsc_nok2 = wave.open("demod_amsc_nok2.wav", "w")

for f in [demod_amsc_ok, demod_amsc_nok, demod_amsc_nok2]:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)

for n in range(0, modulated.getnframes()):
    signal = struct.unpack('h', modulated.readframes(1))[0] / 32768.0
    carrier = math.cos(3000.0 * (n / 44100.0) * math.pi * 2)
    carrier_phased = math.sin(3000.0 * (n / 44100.0) * math.pi * 2)
    carrier_freq = math.cos(3100.0 * (n / 44100.0) * math.pi * 2)

    base = signal * carrier
    base_nok = signal * carrier_phased
    base_nok2 = signal * carrier_freq

    demod_amsc_ok.writeframes(struct.pack('h', base * 32767))
    demod_amsc_nok.writeframes(struct.pack('h', base_nok * 32767))
    demod_amsc_nok2.writeframes(struct.pack('h', base_nok2 * 32767))
