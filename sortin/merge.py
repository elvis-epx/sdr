#!/usr/bin/env python3

import random
n = random.randint(5, 20)
lista = [ random.randint(0, n * 2) for x in range(0, n) ]
print(lista)

def mergesort(lista):
	if len(lista) <= 1:
		return lista
	h = len(lista) // 2

	# Ordena cada metade
	a = mergesort(lista[0:h])
	b = mergesort(lista[h:])

	# Mescla as metades em ordem
	i = 0
	j = 0
	nova = []
	while i < len(a) and j < len(b):
		if a[i] < b[j]:
			nova.append(a[i])
			i += 1
		else:
			nova.append(b[j])
			j += 1
	while i < len(a):
		nova.append(a[i])
		i += 1
	while j < len(b):
		nova.append(b[j])
		j += 1

	return nova
			
lista = mergesort(lista)
print(lista)
if lista != sorted(lista):
	raise Exception("foo")
