CFLAGS=-DDEBUG -DUNDER_TEST -fsanitize=undefined -fstack-protector-strong -fstack-protector-all -std=c++1y -Wall -g -O0 -fprofile-arcs -ftest-coverage

all: test testnet

clean:
	rm -rf *.o test testnet *.gcda *.gcno *.info out *.dSYM

.cpp.o: *.h
	gcc $(CFLAGS) -c $<

test: test.cpp Packet.o Buffer.o Callsign.o Params.o *.h
	gcc $(CFLAGS) -o test test.cpp *.o -lstdc++

testnet: testnet.cpp Handler.o Modifier.o Packet.o Buffer.o Task.o FakeArduino.o Network.o Callsign.o Params.o *.h
	gcc $(CFLAGS) -o testnet testnet.cpp *.o -lstdc++

coverage:
	gcov test.cpp
	gcov testnet.cpp
	lcov -c --directory . --output-file main_coverage.info
	genhtml main_coverage.info --output-directory out
	open out/index.html
