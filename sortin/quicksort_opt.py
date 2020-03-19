#!/usr/bin/env python3

import random
import math

COUNT=1000
a = [ int(random.random() * 1000) for i in range(0, COUNT) ]
print(a)

def quicksort(a, start, end, level):
	length = end - start

	# Use average of 3 as pivot value
	mid = start + length // 2
	pivot_value = (a[start] + a[mid] + a[end-1]) // 3
	print(" " * level + "start=%d end=%d pivot=%d" % (start, end, pivot_value))

	# Scan from both ends until pointers meet
	i = start
	j = end - 1

	# To work correctly with len=2, use i <= j instead of i < j
	while i <= j:
		# print(" " * level + "i=%d(%d) j=%d(%d) start=%d end=%d %s" % (i, a[i], j, a[j], start, end, a[start:end]))
		# Find a big element at left
		while a[i] < pivot_value:
			i += 1
		# Find a small element at right
		while a[j] > pivot_value:
			j -= 1
		# print(" " * level + "   i=%d(%d) j=%d(%d) " % (i, a[i], j, a[j]))
		# and swap them
		# To work correctly with len=2, use i <= j instead of i < j
		if i <= j:
			# print(" " * level + "Swapping %d(%d) and %d(%d)" % (i, a[i], j, a[j]))
			a[i], a[j] = a[j], a[i]
			i += 1
			j -= 1

	print(" " * level + "%s %s" % (a[start:i], a[i:end]))

	# Recursively sort each side with at least 2 elements
	if (start + 1) < i:
		quicksort(a, start, i, level + 1)
	if (i + 1) < end:
		quicksort(a, i, end, level + 1)

quicksort(a, 0, len(a), 0)
print(a)
