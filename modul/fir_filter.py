#!/usr/bin/env python

import wave, struct, numpy
SAMPLE_RATE = 44100

original = wave.open("NubiaCantaDalva.wav", "r")
filter = wave.open("fir_filter.wav", "r")
filtered = wave.open("NubiaFilteredFIR.wav", "w")
filtered.setnchannels(1)
filtered.setsampwidth(2)
filtered.setframerate(SAMPLE_RATE)

n = original.getnframes()
original = struct.unpack('%dh' % n, original.readframes(n))
original = [s / 2.0**15 for s in original]

n = filter.getnframes()
filter = struct.unpack('%di' % n, filter.readframes(n))
filter = [s / 2.0**31 for s in filter]

'''
result = []
# original content is prepended with zeros to simplify convolution logic
original = [0 for i in range(0, len(filter)-1)] + original

for pos in range(len(filter)-1, len(original)):
    # convolution of original * filter
    # i.e. a weighted average of len(filter) past samples
    sample = 0
    for cpos in range(0, len(filter)):
        sample += original[pos - cpos] * filter[cpos]
    result.append(sample)
'''

result = numpy.convolve(original, filter)

result = [ sample * 2.0**15 for sample in result ]
filtered.writeframes(struct.pack('%dh' % len(result), *result))
