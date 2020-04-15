CFLAGS=-DDEBUG -DUNDER_TEST -fsanitize=undefined -fstack-protector-strong -fstack-protector-all -std=c++1y -Wall -g -O0

all: test

clean:
	rm -f *.o test *.gcda *.gcno

.cpp.o: *.h
	gcc $(CFLAGS) -c $<

test: test.cpp Radio.o *.h
	gcc $(CFLAGS) -o test test.cpp *.o -lstdc++
