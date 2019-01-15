#!/usr/bin/env python3

# FM demodulator based on I/Q (quadrature)

import wave, struct, math, random, filters

input_src = wave.open("iq_fm.wav", "r")
FM_CARRIER = 10000.0
MAX_DEVIATION = 1000.0 # Hz

demod = wave.open("iq_fm_demod.wav", "w")
demod.setnchannels(1)
demod.setsampwidth(2)
demod.setframerate(44100)

# Prove we don't need synchronized carrier oscilators
initial_carrier_phase = random.random() * 2 * math.pi

last_angle = 0.0
istream = []
qstream = []

for n in range(0, input_src.getnframes()):
	inputsgn = struct.unpack('h', input_src.readframes(1))[0] / 32768.0

	# I/Q demodulation, not unlike QAM
	carrier = 2 * math.pi * FM_CARRIER * (n / 44100.0) + initial_carrier_phase
	istream.append(inputsgn * math.cos(carrier))
	qstream.append(inputsgn * -math.sin(carrier))

istream = filters.lowpass(istream, 1500) 
qstream = filters.lowpass(qstream, 1500) 

last_output = 0

for n in range(0, len(istream)):
	i = istream[n]
	q = qstream[n]

	# Determine phase (angle) of I/Q pair
	angle = math.atan2(q, i)

	# Change of angle = baseband signal
	# Were you rushing or were you dragging?!
	angle_change = last_angle - angle

	# Just for completeness; big angle changes are not
	# really expected, this is FM, not QAM
	if angle_change > math.pi:
		angle_change -= 2 * math.pi
	elif angle_change < -math.pi:
		angle_change += 2 * math.pi
	last_angle = angle

	# Convert angle change to baseband signal strength
	output = angle_change / (math.pi * MAX_DEVIATION / 44100)
	if abs(output) >= 1:
		# some unexpectedly big angle change happened
		output = last_output
	last_output = output
	
	demod.writeframes(struct.pack('h', int(output * 32767)))
