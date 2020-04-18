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

// Appends Buffer as string (stopping at \0, not at length)
void Buffer::append_str(const Buffer &b)
{
	append(b.cold(), strlen(b.cold()));
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
	if (i >= (signed) this->len) {
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
	unsigned int ai = abs(i);
	if (ai > this->len) {
		ai = this->len;
	}
	unsigned int hi = (i >= 0) ? i : 0;
	if (hi > this->len) {
		hi = this->len;
	}
	
	char *oldbuf = this->buf;
	this->buf = new char[this->len - ai + 1];
	memcpy(this->buf, oldbuf + hi, this->len - ai);
	delete [] oldbuf;

	this->len -= ai;
	this->buf[this->len] = 0;
}

void Buffer::lstrip() {
	while (charAt(0) == ' ') {
		cut(1);
	}
}

void Buffer::rstrip() {
	while (charAt(0) == ' ') {
		cut(-1);
	}
}

void Buffer::strip() {
	lstrip();
	rstrip();
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

bool Buffer::str_equal(const Buffer& cmp) const
{
	return strcmp(cmp.cold()) == 0;
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
	int sz = strlen(mask) * 2;
	Buffer tgt = Buffer(sz);
	va_list args;
	va_start(args, mask);
	while (1) {
		int written = vsnprintf(tgt.hot(), tgt.length(), mask, args);
		if (written <= 0) {
			tgt = "fail";
			break;
		} else if (written >= (signed) tgt.length()) {
			sz *= 2;
			tgt = Buffer(sz);
		} else {
			break;
		}
	}
	va_end(args);

	// makes sure result has length = strlen()
	return Buffer(tgt.cold(), strlen(tgt.cold()));
}


Buffer Buffer::substr(unsigned int start) const
{
	return substr(start, this->len - start);
}

Buffer Buffer::substr(unsigned int start, unsigned int count) const
{
	if (start >= this->len) {
		start = 0;
		count = 0;
	}

	if ((start + count) > this->len) {
		count = this->len - start;
	}

	Buffer copy(count);
	memcpy(copy.hot(), this->buf + start, count);
	return copy;
}
