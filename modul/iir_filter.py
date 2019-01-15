#!/usr/bin/env python

import wave, struct, math
SAMPLE_RATE = 44100

original = wave.open("NubiaCantaDalva.wav", "r")
filtered = wave.open("NubiaFilteredIIR.wav", "w")
filtered.setnchannels(1)
filtered.setsampwidth(2)
filtered.setframerate(SAMPLE_RATE)

# IIR filter coefficients
freq = 2000
r = 0.98
a1 = -2.0 * r * math.cos(freq / (SAMPLE_RATE / 2.0) * math.pi)
a2 = r * r
filter = [a1, a2]
print filter

n = original.getnframes()
original = struct.unpack('%dh' % n, original.readframes(n))
original = [s / 2.0**15 for s in original]

result = [ 0 for i in range(0, len(filter)) ]
biggest = 1
for sample in original:
        for cpos in range(0, len(filter)):
            sample -= result[len(result) - 1 - cpos] * filter[cpos]
        result.append(sample)
        biggest = max(abs(sample), biggest)

result = [ sample / biggest for sample in result ]
result = [ int(sample * (2.0**15 - 1)) for sample in result ]
filtered.writeframes(struct.pack('%dh' % len(result), *result))
