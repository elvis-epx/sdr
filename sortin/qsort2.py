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

	# Acha os limites das listas 'antes' e 'depois' do pivô:
	i = inicio
	j = fim - 1
	while i <= j:
		# Acha elemento fora do lugar à esquerda
		while lista[i] < pivo:
			i += 1
		# Acha elemento fora do lugar à direita
		while lista[j] > pivo:
			j -= 1
		# Troca
		if i <= j:
			lista[i], lista[j] = lista[j], lista[i]
			i += 1
			j -= 1

	# trabalha cada semi-lista
	qsort(lista, inicio, j + 1)
	qsort(lista, i, fim)
	
qsort(lista, 0, len(lista))
print(lista)
if lista != sorted(lista):
	raise Exception("foo")
