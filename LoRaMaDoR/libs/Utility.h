/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifndef _UTILITY_H
#define _UTILITY_H

class Buffer;

class Dict {
public:
	Dict();
	Dict(const Dict &);
	Dict(Dict &&);
	Dict& operator=(const Dict&);
	Dict& operator=(Dict&&);
	~Dict();

	bool has(const char* key) const;
	const char* get(const char* key) const;
	bool put(const Buffer &key);
	bool put(const Buffer& key, const Buffer& value);
	bool put(const Buffer& key, Buffer* value); /* takes ownership of value */
	int count() const;
	void foreach(void* cargo, bool (*f)(const Buffer&, const Buffer*, void *)) const;
	int indexOf(const char *key) const;

private:
	Buffer **keys;
	Buffer **values;
	unsigned int len;
};

class Buffer {
public:
	Buffer();
	Buffer(int len);
	Buffer(const char *, int len);
	Buffer(const char *);
	Buffer(const Buffer&);
	Buffer(Buffer&&);
	Buffer& operator=(const Buffer&);
	Buffer& operator=(Buffer&&);
	~Buffer();

	unsigned int length() const;
	const char* rbuf() const;
	char* wbuf();
	void uppercase();
	void append(const char *s, unsigned int length);

private:
	char *buf;
	unsigned int len;
};

#endif
