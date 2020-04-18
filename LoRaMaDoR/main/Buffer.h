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

	static Buffer sprintf(const char*, ...);
	Buffer substr(unsigned int start) const;
	Buffer substr(unsigned int start, unsigned int end) const;

	bool empty() const;
	unsigned int length() const;
	const char* cold() const;
	char* hot();
	void uppercase();
	bool str_equal(const char *cmp) const;
	bool str_equal(const Buffer &) const;
	int strcmp(const char *cmp) const;
	int strncmp(const char *, unsigned int) const;
	void append(const char *s, unsigned int length);
	void append(const char s);
	void append_str(const Buffer&);
	void cut(int);
	void lstrip();
	void rstrip();
	void strip();
	int indexOf(const char) const;
	int charAt(int) const;

private:
	char *buf;
	unsigned int len;
};

#endif
