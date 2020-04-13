#!/usr/bin/env python3

import random
n = random.randint(5, 20)
lista = [ random.randint(0, n * 2) for x in range(0, n) ]
print(lista)

t = 0
i = 1
while i < len(lista):
	valor = lista[i]
	pos = i - 1
	while lista[pos] > valor and pos >= 0:
		t += 1
		lista[pos + 1] = lista[pos]
		pos -= 1
	lista[pos + 1] = valor
	i += 1

print(lista)
print("%d" % t)
if lista != sorted(lista):
	raise Exception("foo")
