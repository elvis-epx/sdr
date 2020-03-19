#!/usr/bin/env python3

import random
import math

COUNT=16
a = [ int(random.random() * 100) for i in range(0, COUNT) ]
print(a)

def heapify(a, k, root):
	left = root * 2 + 1
	right = left + 1
	largest = root
	if left <= k and a[largest] < a[left]:
		largest = left
	if right <= k and a[largest] < a[right]:
		largest = right
	if largest != root:
		a[root], a[largest] = a[largest], a[root]
		heapify(a, k, largest)

# Create max heap
k = len(a) - 1
for i in range(k // 2, -1, -1):
	heapify(a, k, i)

while k > 0:
	a[k], a[0] = a[0], a[k]
	k -= 1
	heapify(a, k, 0) # Fix heap

print(a)
