#!/usr/bin/env python

import wave, struct, math

baseband = wave.open("paralelepipedo_lopass.wav", "r")
FM_BAND = 1000.0
FM_CARRIER = 44100 / 8.0

fm = wave.open("fm.wav", "w")
fm.setnchannels(1)
fm.setsampwidth(2)
fm.setframerate(44100)

integ_base = 0
for n in range(0, baseband.getnframes()):
    base = struct.unpack('h', baseband.readframes(1))[0] / 32768.0
    # Base signal is integrated
    integ_base += base
    # The FM trick: time (n) is multiplied only by carrier freq;
    # the frequency deviation is added afterwards.
    signal_fm = math.cos(2 * math.pi * FM_CARRIER * (n / 44100.0) +
                         2 * math.pi * FM_BAND * integ_base / 44100.0)
    fm.writeframes(struct.pack('h', signal_fm * 32767))
