CFLAGS=-fsanitize=undefined -fstack-protector-strong -fstack-protector-all -std=c++1y -Wall -g -O0

all: test

clean:
	rm -f *.o test

Utility.o: Utility.cpp *.h
	gcc $(CFLAGS) -c Utility.cpp

Packet.o: Packet.cpp *.h
	gcc $(CFLAGS) -c Packet.cpp

test: test.cpp *.h Packet.o Utility.o
	gcc $(CFLAGS) -o test test.cpp Utility.o Packet.o -lstdc++
