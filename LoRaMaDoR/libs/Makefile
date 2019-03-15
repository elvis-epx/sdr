CFLAGS=-fsanitize=undefined -fstack-protector-strong -fstack-protector-all

all: teste

teste: teste.cpp
	gcc -lstdc++ $(CFLAGS) -o teste teste.cpp
	./teste
