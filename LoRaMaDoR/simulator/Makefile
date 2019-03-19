CFLAGS=-fsanitize=undefined -fstack-protector-strong -fstack-protector-all

all: teste

WString.o: WString.h WString.cpp
	gcc -c $(CFLAGS) WString.cpp

Utility.o: Utility.* WString.h
	gcc -c $(CFLAGS) Utility.cpp

teste: teste.cpp *.o *.h
	gcc -lstdc++ $(CFLAGS) -o teste teste.cpp *.o
	./teste
