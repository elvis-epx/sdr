#!/usr/bin/env python3

import random
import math

COUNT=15
a = [ int(random.random() * 100) for i in range(0, COUNT) ]
print(a)

def quicksort(a, start, end, level):
	length = end - start
	if length <= 1:
		return

	mid = start + length // 2
	pivot_value = (a[start] + a[mid] + a[end-1]) // 3

	# Find pivot point by counting how many elements are <= pivot_value
	# Also, determine minimum and maximum values to handle problem cases
	pivot, lowest, highest = start, start, start
	for i in range(start, end):
		if a[i] <= pivot_value:
			pivot += 1
		if a[i] < a[lowest]:
			lowest = i
		if a[i] > a[highest]:
			highest = i

	if lowest == highest:
		# Pathologcal case: all values are equal; do nothing
		return
	elif pivot == start or pivot == end:
		# Pathological case: badly chosen pivot value
		# Fix by limiting left side to 1 element
		pivot = start + 1
		pivot_value = a[lowest]

	# Move elements bigger than pivot_value to the right side
	j = pivot
	for i in range(start, pivot):
		if a[i] <= pivot_value:
			# This element should stay at left side
			continue
		# If there is a wrong element at left side,
		# there must be a wrong element at right side.
		while a[j] > pivot_value:
			j += 1
		a[i], a[j] = a[j], a[i]

	quicksort(a, start, pivot, level + 1)
	quicksort(a, pivot, end, level + 1)

quicksort(a, 0, len(a), 0)
print(a)
