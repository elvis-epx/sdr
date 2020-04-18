//
// Based on Vector frm
// Zac Staples
// zacstaples (at) mac (dot) com
//

#ifndef __VECTOR_H
#define __VECTOR_H

#include <stddef.h>
#include <string.h>

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
	void insert(unsigned int pos, const T& val);
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

template<class T> 
void Vector<T>::insert(unsigned int pos, const T& val){
	if (pos >= sz || pos < 0) {
		push_back(val);
		return;
	}

	if(space == 0) reserve(4);
	else if(sz==space) reserve(2*space);

	// move pointers
	for (unsigned int i = sz; i > pos; --i) {
		elem[i] = elem[i-1];
	}
	++sz;
	elem[pos] = new T(val);
}

#endif
