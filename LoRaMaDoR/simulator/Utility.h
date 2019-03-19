/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include "WString.h"

struct StringPair {
	StringPair(const String& pa, const String& pb): a(pa), b(pb) {}
	String a() const;
	String b() const;
	String _a;
	String _b;
};

struct Dict {
	Dict();
	bool has(const char *key) const;
	bool has(const String& key) const;
	String get(const char *key) const;
	String get(const String& key) const;
	bool put(const String& key, const String& value);
	int length() const;

	StringPair *contents;
	int len;
};

struct Buffer {
	Buffer(const char *mbuf, int len);
	char *buf;
	int len;
};
