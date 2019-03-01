# cython: language_level=3

# Does FM stereo decoding. Implements a PLL to generate the
# stereo carrier using the pilot tone as reference.

import math

tau = 2 * math.pi

def demod_stereo(output_jstereo_mod, pll, STEREO_CARRIER,
		INPUT_RATE, detected_pilot, last_pilot,
		deviation_avg, last_deviation_avg):

	output_jstereo = [ 0.0 for i in range(0, len(output_jstereo_mod)) ]

	for n in range(0, len(output_jstereo_mod)):
		# Advance carrier
		pll = (pll + tau * STEREO_CARRIER / INPUT_RATE) % tau

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
			deviation -= tau
		deviation_avg = 0.99 * deviation_avg + 0.01 * deviation
		rotation = deviation_avg - last_deviation_avg
		last_deviation_avg = deviation_avg

		if abs(deviation_avg) > math.pi / 8:
			pll = ideal
			pll = (pll + tau * STEREO_CARRIER / INPUT_RATE) % tau
			deviation_avg = 0.0
			last_deviation_avg = 0.0

		STEREO_CARRIER /= (1 + (rotation * 1.05) / tau)

	return output_jstereo, pll, STEREO_CARRIER, \
		last_pilot, deviation_avg, last_deviation_avg
