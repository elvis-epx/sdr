//*********************************************************************************
//    Lightweight Arduino Compatible implementation of key STL Vector methods
//*********************************************************************************
//
// Zac Staples
// zacstaples (at) mac (dot) com
//
// 13 June 2014...Friday the 13th...therfore this is probably broken
//
// I needed a data structure to hold refernces and/or pointers as a data
// member of an abstract class for sensors on my robot.  That's the point
// I decided I wanted the basic implementation of the STL vector available 
// to me in my Arduino sketches.  This is not a complete implementation of
// the STL vector, but is designed to be "good enough" to take sketches
// further into OOP.
//
// Based on Stroustrup's basic implementation of vector in Programming 3rd
// edition page 656 and his Simple allocator from The c++ programming 
// language, 4th edition.  However, I needed info from the following sources
// to implement to allocator to correctly handle placement new in 
// the AVR/Arduino environment.
//
// http://www.codeproject.com/Articles/4795/C-Standard-Allocator-An-Introduction-and-Implement
// http://www.glenmccl.com/nd_cmp.htm
// http://www.sourcetricks.com/2008/05/c-placement-new.html#.U5yJF41dW0Q
// http://stackoverflow.com/questions/9805829/arduino-c-destructor
// http://arduino.land/FAQ/index.php?solution_id=1023
//
// Released on the beer license...if this works for you...then remember my
// name an buy me a beer sometime.

#ifndef VECTOR_H
#define VECTOR_H JUN_2014

#include <stddef.h>

template<class T>
class Vector {
	unsigned int sz;
	T** elem;
	unsigned int space;
	Vector(const Vector&);

public:
	Vector() : sz(0), elem(0), space(0) {}
	Vector(const int s) : sz(0) {
		reserve(s);
	}
	
	Vector& operator=(const Vector&);
	Vector& operator=(Vector&&);
	Vector(const Vector&&);
	
	~Vector() { 
		clear();
	}
	
	void clear();
	T& operator[](int n) { return *elem[n]; }
	const T& operator[](int n) const { return *elem[n]; }
	
	unsigned int size() const { return sz; }
	unsigned int capacity() const { return space; }
	
	void reserve(unsigned int newalloc);
	void push_back(const T& val);
	void remov(unsigned int pos);
};

template<class T> 
Vector<T>& Vector<T>::operator=(const Vector& a) {
	if (this==&a) return *this;

	clear();

	// new array
	elem = new T*[a.size()];
	space = sz = a.size();

	// copy elements
	for(unsigned int i=0; i < sz; ++i) {
		elem[i] = new T(a[i]);
	}

	return *this;
}

template<class T> 
void Vector<T>::clear()
{
	for (unsigned int i=0; i<sz; ++i) delete elem[i];
	delete [] elem;
	elem = 0;
	sz = space = 0;
}

template<class T> 
Vector<T>& Vector<T>::operator=(Vector&& a) {
	if(this==&a) return *this;

	clear();

	elem = a.elem;
	sz = a.sz;
	space = a.sz;

	a.elem = 0;
	a.sz = 0;
	a.space = 0;
}

template<class T> void Vector<T>::reserve(unsigned int newalloc){
	if(newalloc <= space) return;

	T** p = new T*[newalloc];
	if (elem) {
		memcpy(p, elem, sizeof(T*) * sz);
		delete [] elem;
	}
	elem = p;
	space = newalloc;	
}

template<class T> void
Vector<T>::remov(unsigned int pos){
	if (pos >= 0 && pos < sz) {
		delete elem[pos];
		--sz;
		// move pointers
		for (unsigned int i = pos; i < sz; ++i) {
			elem[i] = elem[i+1];
		}
	}
}

template<class T> 
void Vector<T>::push_back(const T& val){
	if(space == 0) reserve(4);				//start small
	else if(sz==space) reserve(2*space);
	elem[sz] = new T(val);
	++sz;
}

#endif
