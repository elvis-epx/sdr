#!/usr/bin/env python3

import random

lista = [4, 7, 3, 8, 6, 1, 2, 5]
print(lista)

c = 0
for i in range(1, len(lista)):
	j = i - 1
	while j >= 0 and lista[j] > lista[j + 1]:
		print(j, i, lista[j], lista[j + 1], lista)
		lista[j + 1], lista[j] = lista[j], lista[j + 1]
		j -= 1
		c += 1

print(lista)
print("%d ciclos" % c)
