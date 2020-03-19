#!/usr/bin/env python3

import random
import math

COUNT=12
a = [ int(random.random() * 100) for i in range(0, COUNT) ]
print(a)

def quicksort(a, start, end, level):
	length = end - start
	if length <= 1:
		return
	print(" " * level, a[start:end])

	# Use average of 3 as pivot value
	mid = start + length // 2
	pivot_value = (a[start] + a[mid] + a[end-1]) // 3

	# Scan from both ends until pointers meet
	i, j = start, end - 1
	# Logic is carefully crafted to handle lists with size=2
	# and uniform lists
	while i <= j:
		while a[i] < pivot_value:
			i += 1
		while a[j] > pivot_value:
			j -= 1
		if i <= j:
			a[i], a[j] = a[j], a[i]
			i += 1
			j -= 1

	quicksort(a, start, i, level + 1)
	quicksort(a, i, end, level + 1)

quicksort(a, 0, len(a), 0)
print(a)
