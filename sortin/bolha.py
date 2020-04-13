#!/usr/bin/env python3

import random
n = random.randint(5, 20)
lista = [ random.randint(0, n * 2) for x in range(0, n) ]
print(lista)

t = 0
sujo = True
while sujo:
	sujo = False
	i = 0
	while i < len(lista) - 1:
		t += 1
		if lista[i] > lista[i + 1]:
			lista[i], lista[i + 1] = lista[i + 1], lista[i]
			sujo = True
		i += 1

print(lista)
print("%d comparações" % t)
if lista != sorted(lista):
	raise Exception("foo")
