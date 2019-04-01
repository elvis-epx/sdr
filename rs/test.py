#!/usr/bin/env python3

from decimalrs import * 
from random import random
import sys

k = 7
weakened = False
rs = DecimalRS(k, weakened)
msg_digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
rs_digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "X"]

false_oks = 0
false_oks_base = 0
false_oks_2 = 0
false_oks_2_base = 0

for i in range(0, 100000):
	number = int(random() * 10 ** k)
	encoded = rs.encode(number)
	decode_res = rs.decode(encoded)
	assert(decode_res[0] == number and decode_res[1] == 0)
	
	# Generate a list of errors
	error_count = 1 + int(random() * 4)
	errors = {}
	b = 0
	while len(errors) < error_count:
		b = (b + 1) % len(encoded)
		if b in errors:
			continue
		if random() > 0.1:
			continue
		if b < k or weakened:
			digits = msg_digits
		else:
			digits = rs_digits
		while True:
			aa = int(random() * len(digits))
			a = digits[aa]
			if a != encoded[b]:
				errors[b] = a
				break

	# Apply errors
	corrupted = encoded
	for b, a in errors.items():
		corrupted = corrupted[:b] + a + corrupted[b+1:]

	# Test decoding
	decoded, status = rs.decode(corrupted)
	assert(error_count > 2 or status != DecimalRS.NO_ERRORS)
	if error_count == 1:
		assert(decoded == number and (status == DecimalRS.DIGIT or status == DecimalRS.CORRECTED))
	elif error_count == 2:
		if status != DecimalRS.UNCORRECTABLE:
			false_oks_2 += 1
			'''
			print("False ok ", number, encoded, error_count, \
				corrupted, decoded, status)
			'''
		false_oks_2_base += 1
	else:
		if status != DecimalRS.UNCORRECTABLE:
			false_oks += 1
		false_oks_base += 1

print("False corrections: %d of %d (%f%%) multiple-error decodes" % (false_oks, false_oks_base, 100.0 * false_oks / false_oks_base))
print("False corrections: %d of %d (%f%%) two-error decodes" % (false_oks_2, false_oks_2_base, 100.0 * false_oks_2 / false_oks_2_base))
