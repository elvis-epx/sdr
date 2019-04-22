CFLAGS=-fsanitize=undefined -fstack-protector-strong -fstack-protector-all -std=c++1y -Wall -g -O0

all: test testnet

clean:
	rm -f *.o test

.cpp.o:
	gcc $(CFLAGS) -c $<

test: test.cpp Handler.o Modifier.o Packet.o Buffer.o Task.o FakeArduino.o Network.o *.h
	gcc $(CFLAGS) -o test test.cpp *.o -lstdc++

testnet: testnet.cpp Handler.o Modifier.o Packet.o Buffer.o Task.o FakeArduino.o Network.o *.h
	gcc $(CFLAGS) -o testnet testnet.cpp *.o -lstdc++
