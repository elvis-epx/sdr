CFLAGS=-fsanitize=undefined -fstack-protector-strong -fstack-protector-all -std=c++1y -Wall

all: teste

clean:
	rm -f *.o teste

WString.o: WString.cpp WString.h
	gcc $(CFLAGS) -c WString.cpp

Utility.o: Utility.cpp *.h
	gcc $(CFLAGS) -c Utility.cpp

Packet.o: Packet.cpp *.h
	gcc $(CFLAGS) -c Packet.cpp

teste: teste.cpp *.h Packet.o Utility.o WString.o
	gcc -lstdc++ $(CFLAGS) -o teste teste.cpp WString.o Utility.o Packet.o
