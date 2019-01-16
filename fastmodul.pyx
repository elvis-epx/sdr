# cython: language_level=3

import math

def get_angles(samples):
	# Finds angles (phase) of I/Q pairs
	return [
		math.atan2(
			(int(samples[n * 2 + 0]) - 127.5) / 128.0, 
			(int(samples[n * 2 + 1]) - 127.5) / 128.0
		) for n in range(0, len(samples) // 2) ]
