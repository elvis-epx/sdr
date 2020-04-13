#!/usr/bin/env python3

import random
n = random.randint(5, 20)
lista = [ random.randint(0, n * 2) for x in range(0, n) ]
print(lista)

def qsort(lista, inicio, fim):
	if (fim - inicio) <= 1:
		return
	
	# Escolhe pivo
	pivo = lista[random.randint(inicio, fim - 1)]

	# Conta elementos que devem ficar à esquerda do pivô
	menores = 0
	iguais = 0
	i = inicio
	while i < fim:
		if lista[i] < pivo:
			menores += 1
		elif lista[i] == pivo:
			iguais += 1
		i += 1

	# Caso fortuito: todos os elementos são iguais ao pivô
	# (provocaria recursão infinita)
	if iguais == (fim - inicio):
		return

	# Transfere elementos que estão do lado errado
	i = inicio
	imax = j = inicio + menores
	while i < imax and j < fim:
		if lista[i] < pivo:
			i += 1
		elif lista[j] >= pivo:
			j += 1
		else:
			lista[i], lista[j] = lista[j], lista[i]
			i += 1
			j += 1

	# trabalha cada semi-lista
	qsort(lista, inicio, inicio + menores)
	qsort(lista, inicio + menores, fim)
	
qsort(lista, 0, len(lista))
print(lista)

if lista != sorted(lista):
	raise Exception("foo")

