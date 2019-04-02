/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifndef __BUFFER_H
#define __BUFFER_H

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
	const char* cold() const;
	char* hot();
	void uppercase();
	bool str_equal(const char *cmp) const;
	void append(const char *s, unsigned int length);

private:
	char *buf;
	unsigned int len;
};

#endif
