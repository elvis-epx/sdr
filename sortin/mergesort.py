#!/usr/bin/env python3

import random
import math

COUNT=16
a = [ int(random.random() * 100) for i in range(0, COUNT) ]
print(a)

def mergesort(a):
	if len(a) <= 1:
		return

	# Copy and sort semi-parts recursively
	mid = len(a) // 2
	left, right = a[0:mid], a[mid:]
	mergesort(left)
	mergesort(right)

	# merge sorted semi-parts into original array
	l, r = 0, 0
	for i in range(0, len(a)):
		if l >= len(left): # left part empty
			a[i] = right[r]
			r += 1
		elif r >= len(right): # right part empty
			a[i] = left[l]
			l += 1
		elif left[l] < right[r]:
			a[i] = left[l]
			l += 1
		else:
			a[i] = right[r]
			r += 1

mergesort(a)
print(a)
