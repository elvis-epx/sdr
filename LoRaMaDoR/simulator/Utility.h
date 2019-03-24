/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

struct Dict {
	Dict();
	Dict(const Dict &);
	Dict(Dict &&);
	Dict& operator=(const Dict&);
	Dict& operator=(Dict&&);
	~Dict();

	bool has(const char* key) const;
	const char* get(const char* key) const;
	bool put(const char* key);
	bool put(const char* key, const char* value);
	int count() const;
	void foreach(void* cargo, bool (*f)(const char*, const char*, void *)) const;
	int indexOf(const char *key) const;

	char **keys;
	char **values;
	int len;
};

struct Buffer {
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

private:
	char *buf;
	unsigned int len;
};

void uppercase(char *);

