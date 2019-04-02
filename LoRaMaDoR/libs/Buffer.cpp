/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include <stdlib.h>
#include <string.h>
#include "Buffer.h"

Buffer::Buffer()
{
	this->len = 0;
	this->buf = new char[0];
}

Buffer::Buffer(int len)
{
	this->len = len;
	this->buf = new char[len + 1];
	memset(this->buf, 0, len + 1);
}

Buffer::Buffer(Buffer&& moved)
{
	delete [] this->buf;

	this->len = moved.len;
	this->buf = moved.buf;
	moved.len = 0;
	moved.buf = 0;
}

Buffer::Buffer(const Buffer& model)
{
	this->len = model.len;
	this->buf = new char[this->len + 1];
	memcpy(this->buf, model.buf, this->len);
	this->buf[len] = 0;
}

Buffer& Buffer::operator=(Buffer&& moved)
{
	delete [] this->buf; 

	this->len = moved.len;
	this->buf = moved.buf;
	moved.len = 0;
	moved.buf = 0;

	return *this;
}

Buffer& Buffer::operator=(const Buffer& model)
{
	delete [] buf;

	len = model.len;
	buf = new char[len + 1];
	memcpy(buf, model.buf, len);
	buf[len] = 0;

	return *this;
}

void Buffer::append(const char *s, unsigned int add_length)
{
	if (!s) {
		return;
	}

	char *oldbuf = this->buf;
	this->buf = new char[this->len + add_length + 1];
	memcpy(this->buf, oldbuf, this->len);
	delete [] oldbuf;

	memcpy(this->buf + this->len, s, add_length);
	this->buf[this->len + add_length] = 0;
	this->len += add_length;
}

Buffer::~Buffer()
{
	if (this->buf) {
		delete [] this->buf;
		this->buf = 0;
	}
	this->len = 0;
}

Buffer::Buffer(const char *buf, int len)
{
	this->len = len;
	this->buf = new char[len + 1];
	if (buf) {
		memcpy(this->buf, buf, len);
	}
	this->buf[len] = 0;
}

Buffer::Buffer(const char *s)
{
	len = strlen(s);
	buf = new char[len + 1];
	memcpy(buf, s, len);
	buf[len] = 0;
}

const char* Buffer::cold() const
{
	return buf;
}

char* Buffer::hot()
{
	return buf;
}

unsigned int Buffer::length() const
{
	return len;
}

void Buffer::uppercase()
{
	for (unsigned int i = 0; i < len; ++i) {
		if (buf[i] >= 'a' && buf[i] <= 'z') {
			buf[i] += 'A' - 'a';
		}
	}
}

bool Buffer::str_equal(const char *cmp) const
{
	return strncmp(cmp, buf, len) == 0;
}

int Buffer::strcmp(const char *cmp) const
{
	return strncmp(cmp, buf, len);
}
