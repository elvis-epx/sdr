#!/usr/bin/env python3

import random
import math

COUNT=1000
a = [ int(random.random() * 1000) for i in range(0, COUNT) ]
print(a)

def quicksort(a, start, end, level):
	print(" " * level + "start=%d end=%d %s" % (start, end, str(a[start:end])))
	length = end - start

	# Use average of 3 as pivot value
	mid = start + length // 2
	pivot_value = (a[start] + a[mid] + a[end-1]) // 3

	# Count how many elements are <= pivot, also min and max
	pivot = start
	lowest = start
	lowest_value = a[start]
	highest = start
	highest_value = a[start]
	for i in range(start, end):
		if a[i] <= pivot_value:
			pivot += 1
		if a[i] < lowest_value:
			lowest_value = a[i]
			lowest = i
		if a[i] > highest_value:
			highest_value = a[i]
			highest = i

	print(" " * level + "pivot=%d, pivot_value=%d" % (pivot, pivot_value))

	if lowest == highest:
		print(" " * level + "all equal")
		return

	if pivot == start or pivot == end:
		pivot = start + 1
		pivot_value = lowest_value
		print(" " * level + "pathological")

	# Move elements > pivot to the right side
	j = pivot
	for i in range(start, pivot):
		if a[i] > pivot_value:
			# Find element <= pivot at right side
			while a[j] > pivot_value:
				j += 1
			# Exchange
			a[i], a[j] = a[j], a[i]
	print(" " * level + "after move: %s %s" % (str(a[start:pivot]), str(a[pivot:end])))

	# Recursively sort each side with at least 2 elements
	if (start + 1) < pivot:
		quicksort(a, start, pivot, level + 1)
	if (pivot + 1) < end:
		quicksort(a, pivot, end, level + 1)

quicksort(a, 0, len(a), 0)
print(a)
