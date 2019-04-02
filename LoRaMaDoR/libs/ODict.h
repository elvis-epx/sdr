/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifndef _ODICT_H
#define _ODICT_H

#include <Utility.h>

template <class T> class ODict {
public:
	ODict() {
		keys = new Buffer[0];
		values = new T[0];
	}

	ODict(const ODict &) = delete;

	ODict(Dict&& model) {
		delete [] keys;
		delete [] values;
		keys = model.keys;
		values = model.values;
		model.keys = 0;
		model.values = 0;	
	}

	ODict& operator=(const ODict&) = delete;

	ODict& operator=(ODict&&) {
		delete [] keys;
		delete [] values;
		keys = model.keys;
		values = model.values;
		model.keys = 0;
		model.values = 0;	
	}

	~Dict() {
		delete [] keys;
		delete [] values;
	}

	bool has(const char* key) const {
		return indexOf(key) != -1;
	}

	T get(const char* key) const {
		return values[indexOf(key)];
	}

	bool put(const char *akey, const T& value) {
		Buffer key = Buffer(akey);
		key.uppercase();

		int pos = indexOf(key.rbuf());
		bool ret = false;

		if (pos <= -1) {
			len += 1;
			Buffer old_keys[] = keys;
			T old_values[] = values;
			keys = new Buffer[len];
			values = new T[len];
			for (unsigned int i = 0; i < (len - 1); ++i) {
				keys[i] = old_keys[i];
				values[i] = old_values[i];
			}
			delete [] old_keys;
			delete [] old_values;
			pos = len - 1;
			ret = true;
		}
	
		keys[pos] = key;
		values[pos] = value;

		return ret;
	}

	int count() const {
		return len;
	}

	void foreach(void* cargo, bool (*f)(const Buffer&, const T&, void *)) const {
		for (unsigned int i = 0; i < len; ++i) {
			if (! f(keys[i], values[i], cargo)) {
				break;
			}
		}
	}

	int indexOf(const char *key) const {
		for (unsigned int i = 0; i < len; ++i) {
			if (0 == strcmp(key, keys[i]->rbuf())) {
				return i;
			}
		}
	}

	return -1;

private:
	Buffer keys[];
	T values[];
	unsigned int len;
};

#endif
