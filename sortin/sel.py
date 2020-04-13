#!/usr/bin/env python3

import random
n = random.randint(5, 20)
lista = [ random.randint(0, n * 2) for x in range(0, n) ]
print(lista)

i = 0
while i < len(lista) - 1:
	j = i + 1
	while j < len(lista):
		if lista[i] > lista[j]:
			lista[i], lista[j] = lista[j], lista[i]
		j += 1
	i += 1

print(lista)
if lista != sorted(lista):
	raise Exception("foo")
