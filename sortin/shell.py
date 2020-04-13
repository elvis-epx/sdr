#!/usr/bin/env python3

import random
n = random.randint(5, 20)
lista = [ random.randint(0, n * 2) for x in range(0, n) ]
print(lista)

t = 0
gaps = [ 5, 3, 2, 1 ]
for gap in gaps:
	i = gap
	while i < len(lista):
		valor = lista[i]
		pos = i - gap
		while lista[pos] > valor and pos >= 0:
			t += 1
			lista[pos + gap] = lista[pos]
			pos -= gap
		lista[pos + gap] = valor
		i += 1

print(lista)
print("%d" % t)
if lista != sorted(lista):
	raise Exception("foo")
