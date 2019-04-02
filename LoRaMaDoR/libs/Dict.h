/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifndef _ODICT_H
#define _ODICT_H

#include "Vector.h"
#include "Buffer.h"

template <class T> class Dict {
public:
	Dict() {}

	Dict(const Dict& model) {
		keys = model.keys;
		values = model.values;
	}

	Dict& operator=(const Dict& model) {
		keys = model.keys;
		values = model.values;
		return *this;
	}

	~Dict() {}

	bool has(const char* key) const {
		return indexOf(key) != -1;
	}

	bool has(const Buffer& key) const {
		return indexOf(key) != -1;
	}

	T get(const char* key) const {
		return values[indexOf(key)];
	}

	T get(const Buffer& key) const {
		return values[indexOf(key)];
	}

	bool put(const Buffer &akey, const T& value) {
		return put(akey.cold(), value);
	}

	bool put(const char *akey, const T& value) {
		Buffer key = Buffer(akey);
		key.uppercase();

		int pos = indexOf(key.cold());
		bool ret = false;

		if (pos <= -1) {
			keys.push_back(key);
			values.push_back(value);
		} else {
			keys[pos] = key;	
			values[pos] = value;
		}
	
		return ret;
	}

	int count() const {
		return keys.size();
	}

	void foreach(void* cargo, bool (*f)(const Buffer&, const T&, void *)) const {
		for (unsigned int i = 0; i < keys.size(); ++i) {
			if (! f(keys[i], values[i], cargo)) {
				break;
			}
		}
	}

	int indexOf(const Buffer &key) const {
		return indexOf(key.cold());
	}

	int indexOf(const char *key) const {
		for (unsigned int i = 0; i < keys.size(); ++i) {
			if (keys[i].str_equal(key)) {
				return i;
			}
		}
		return -1;
	}

private:
	Vector<Buffer> keys;
	Vector<T> values;
};

#endif
