# cython: language_level=3

import math

def get_angles(samples):
	# Finds angles (phase) of I/Q pairs
	return [
		math.atan2(
			(int(samples[n * 2 + 0]) - 127.5) / 128.0, 
			(int(samples[n * 2 + 1]) - 127.5) / 128.0
		) for n in range(0, len(samples) // 2) ]


def demod_stereo(output_jstereo_mod, pll, STEREO_CARRIER, INPUT_RATE, detected_pilot,
					last_pilot, deviation_avg, last_deviation_avg):

	output_jstereo = [ 0 for i in range(0, len(output_jstereo_mod)) ]

	for n in range(0, len(output_jstereo_mod)):
		# Advance carrier
		pll = (pll + 2 * math.pi * STEREO_CARRIER / INPUT_RATE) % (2 * math.pi)

		# Standard demodulation
		output_jstereo[n] = math.cos(pll) * output_jstereo_mod[n]

		############ PLL #################

		cur_pilot = detected_pilot[n]
		zero_crossed = (cur_pilot * last_pilot) <= 0
		last_pilot = cur_pilot
		if not zero_crossed:
			continue

		ideal = math.pi
		deviation = pll - ideal
		if deviation > math.pi:
			deviation -= 2 * math.pi
		deviation_avg = 0.99 * deviation_avg + 0.01 * deviation
		rotation = deviation_avg - last_deviation_avg
		last_deviation_avg = deviation_avg

		if abs(deviation_avg) > math.pi / 8:
			pll = ideal
			pll = (pll + 2 * math.pi * STEREO_CARRIER / INPUT_RATE) % 2 * math.pi
			deviation_avg = 0.0
			last_deviation_avg = 0.0
		
		STEREO_CARRIER -= rotation * 200

	return output_jstereo, pll, STEREO_CARRIER, \
		last_pilot, deviation_avg, last_deviation_avg
