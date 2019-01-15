#!/usr/bin/env python

import wave
import struct
import math

modulated = wave.open("amssb_hilbert.wav", "r")

demod_amssb_ok = wave.open("demod_amssb_hilbert_ok.wav", "w")
demod_amssb_nok = wave.open("demod_amssb_hilbert_nok.wav", "w")
demod_amssb_nok2 = wave.open("demod_amssb_hilbert_nok2.wav", "w")

for f in [demod_amssb_ok, demod_amssb_nok, demod_amssb_nok2]:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)

for n in range(0, modulated.getnframes()):
    signal = struct.unpack('h', modulated.readframes(1))[0] / 32768.0
    carrier = math.cos(3000.0 * (n / 44100.0) * math.pi * 2)
    carrier_phased = math.cos(3000.0 * (n / 44100.0) * math.pi * 2 + math.pi / 3)
    carrier_freq = math.cos(3100.0 * (n / 44100.0) * math.pi * 2)

    base = signal * carrier
    base_nok = signal * carrier_phased
    base_nok2 = signal * carrier_freq

    demod_amssb_ok.writeframes(struct.pack('h', base * 32767))
    demod_amssb_nok.writeframes(struct.pack('h', base_nok * 32767))
    demod_amssb_nok2.writeframes(struct.pack('h', base_nok2 * 32767))
