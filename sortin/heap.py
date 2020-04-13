#!/usr/bin/env python3

import random
n = random.randint(5, 20)
lista = [ random.randint(0, n * 2) for x in range(0, n) ]
print(lista)

def heapify(tamanho, topo):
	folha_esq = topo * 2 + 1
	folha_dir = folha_esq + 1
	maior = topo
	# Determina quem é maior, entre topo e folhas
	if folha_esq < tamanho and lista[folha_esq] > lista[maior]:
		maior = folha_esq
	if folha_dir < tamanho and lista[folha_dir] > lista[maior]:
		maior = folha_dir
	if maior != topo:
		# Troca
		lista[maior], lista[topo] = lista[topo], lista[maior]
		# Recursão no galho afetado pela troca
		heapify(tamanho, maior)

# Primeiro arranjo
tamanho = len(lista)
i = len(lista) // 2 - 1
while i > 0:
	heapify(tamanho, i)
	i -= 1

while tamanho > 1:
	# Conserta árvore
	heapify(tamanho, 0)
	# Saca topo da árvore
	lista[0], lista[tamanho - 1] = lista[tamanho - 1], lista[0]
	tamanho -= 1

if lista != sorted(lista):
	raise Exception("foo")

print(lista)
