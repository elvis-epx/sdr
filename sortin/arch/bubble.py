#!/usr/bin/env python3

import random

lista = [4, 7, 3, 8, 6, 1, 2, 5]
print(lista)

def verifica(li):
	for i in range(0, len(li) - 1):
		if li[i] > li[i + 1]:
			return False
	return True

n = 0
c = 0
while not verifica(lista):
	n += 1
	for i in range(0, len(lista) - 1):
		if lista[i] > lista[i + 1]:
			lista[i], lista[i + 1] = lista[i + 1], lista[i]
		c += 1

print(lista)
print("%d tentativas" % n)
print("%d ciclos" % c)
