#!/usr/bin/env python

import wave, struct, math, numpy

hlen = 500.0

hilbert_impulse = [ (1.0 / (math.pi * t / hlen)) \
			for t in range(int(-hlen), 0) ]
hilbert_impulse.extend([0])
hilbert_impulse.extend( [ (1.0 / (math.pi * t / hlen)) \
			for t in range(1, int(hlen+1)) ] )

hilbert_impulse = [ x * 1.0 / hlen for x in hilbert_impulse ]

baseband = wave.open("amssb_hilbert_orig.wav", "r")
amssbh = wave.open("amssb_hilbert.wav", "w")

for f in [amssbh]:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)

base = []
base.extend([ struct.unpack('h', baseband.readframes(1))[0] / 32768.0 \
		for n in range(0, baseband.getnframes()) ])
base.extend([ 0 for n in range(0, int(hlen)) ])

base_hilbert = numpy.convolve(base[:], hilbert_impulse)

for n in range(0, len(base) - int(hlen)):
    carrier_cos = math.cos(3000.0 * (n / 44100.0) * math.pi * 2)
    carrier_sin = -math.sin(3000.0 * (n / 44100.0) * math.pi * 2)

    s1 = base[n] * carrier_cos
    # time-shifted signal because Hilbert transform is noncausal
    s2 = base_hilbert[n + int(hlen)] * carrier_sin

    signal_amssbh = s1 + s2

    amssbh.writeframes(struct.pack('h', signal_amssbh * 32767))
