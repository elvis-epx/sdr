/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <cstring>
#include <stdarg.h>
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

void Buffer::append(const char c)
{
	char *oldbuf = this->buf;
	this->buf = new char[this->len + 2];
	memcpy(this->buf, oldbuf, this->len);
	delete [] oldbuf;

	this->buf[this->len] = c;
	this->buf[this->len + 1] = 0;
	this->len += 1;
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
	return this->buf;
}

char* Buffer::hot()
{
	return this->buf;
}

unsigned int Buffer::length() const
{
	return this->len;
}

int Buffer::charAt(int i) const
{
	if (i < 0) {
		i = this->len + i;
	}
	if (i >= this->len) {
		return -1;
	}
	return this->buf[i];
}


int Buffer::indexOf(char c) const
{
	for (unsigned int i = 0; i < this->len; ++i) {
		if (this->buf[i] == c) {
			return i;
		}
	}
	return -1;
}

void Buffer::cut(int i)
{
	unsigned int ai = i > 0 ? i : -i;
	unsigned int hi = i > 0 ? i : 0;
	char *oldbuf = this->buf;
	this->buf = new char[this->len - ai + 1];
	memcpy(this->buf, oldbuf + hi, this->len - ai);
	delete [] oldbuf;

	this->len -= ai;
	this->buf[this->len + 1] = 0;
}

bool Buffer::empty() const {
	return this->len == 0;
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
	return strcmp(cmp) == 0;
}

int Buffer::strcmp(const char *cmp) const
{
	return std::strcmp(cmp, buf);
}

int Buffer::strncmp(const char *cmp, unsigned int len) const
{
	return std::strncmp(cmp, buf, len);
}

Buffer Buffer::sprintf(const char *mask, ...)
{
	va_list args;
	va_start(args, mask);
	int tot = strlen(mask) * 2;
	while (1) {
		Buffer tgt(tot);
		int written = snprintf(tgt.hot(), tgt.length() - 1, mask, args);
		if (written <= 0) {
			return "";
		} else if (written >= tot) {
			return tgt;
		}
		tot *= 2;
	}
	va_end(args);
}

