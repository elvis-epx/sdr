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

	const T& get(const char* key) const {
		return values[indexOf(key)];
	}

	const T& operator[](const char* key) const {
		return values[indexOf(key)];
	}

	const T& get(const Buffer& key) const {
		return values[indexOf(key)];
	}

	T& operator[](const char* key) {
		if (!has(key)) {
			put(key, T());
		}
		return values[indexOf(key)];
	}

	bool put(const Buffer &akey, const T& value) {
		return put(akey.cold(), value);
	}

	bool put(const char *akey, const T& value) {
		Buffer key = Buffer(akey);
		key.uppercase();

		int pos = indexOf(key.cold());
		bool new_key = pos <= -1;

		if (new_key) {
			int insertion_pos = indexOf(key.cold(), 0, keys.size(), false);
			keys.insert(insertion_pos, key);
			values.insert(insertion_pos, value);
		} else {
			keys[pos] = key;	
			values[pos] = value;
		}
	
		return new_key;
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

	int indexOf(const char *key, unsigned int from, unsigned int to, bool exact) const {
		if ((to - from) <= 3) {
			// linear search
			for (unsigned int i = from; i < to; ++i) {
				int cmp = keys[i].strcmp(key);
				if (cmp == 0) {
					// good for exact and non-exact queriers
					return i;
				} else if ((! exact) && (cmp < 0)) {
					// non-exact, looks for insertion point
					return i;
				}
			}

			return exact ? -1 : to;
		}

		// recursive binary search
		unsigned int middle = (from + to) / 2;
		int cmp = keys[middle].strcmp(key);
		if (cmp == 0) {
			return middle;
		} else if (cmp < 0) {
			// key A, middle key N, look into left
			return indexOf(key, from, middle, exact);
		} else {
			// key Z, middle key N, look into right 
			return indexOf(key, middle + 1, to, exact);
		}

		return -1;
	}

	int indexOf(const Buffer &key) const {
		return indexOf(key.cold(), true);
	}

	int indexOf(const char *key) const {
		return indexOf(key, 0, keys.size(), true);
	}

private:
	Vector<Buffer> keys;
	Vector<T> values;
};

#endif
