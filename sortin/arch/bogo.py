#!/usr/bin/env python3

import random

lista = [4, 7, 3, 8, 6, 1, 2, 5]
print(lista)

# O(n) - linear
def em_ordem():
	i = 0
	while i < len(lista) - 1:
		if lista[i] > lista[i + 1]:
			return False
		i += 1
	return True

t = 0

while not em_ordem():
	random.shuffle(lista)
	t += 1

print(lista)
print("%d tentativas" % t)
