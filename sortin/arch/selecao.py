#!/usr/bin/env python3

import random

lista = [4, 7, 3, 8, 6, 1, 2, 5]
print(lista)

c = 0
for i in range(0, len(lista) - 1):
	for j in range(i, len(lista)):
		if lista[i] > lista[j]:
			lista[i], lista[j] = lista[j], lista[i]
		c += 1

print(lista)
print("%d ciclos" % c)
