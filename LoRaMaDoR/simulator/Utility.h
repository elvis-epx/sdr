/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include "WString.h"

struct Dict {
	Dict();
	Dict(const Dict &);
	Dict& operator=(const Dict &) = delete;
	bool operator==(const Dict &) = delete;

	bool has(const String& key) const;
	const String* get(const String& key) const;
	bool put(const String& key, const String* value);
	int length() const;
	void foreach(void* cargo, bool (*f)(const String&, const String*, void *)) const;
	int indexOf(const String &key) const;

	String **keys;
	String **values;
	int len;
};

struct Buffer {
	Buffer(int len);
	Buffer(const char *mbuf, int len);
	char *buf;
	int len;
	String Str() const;
};
