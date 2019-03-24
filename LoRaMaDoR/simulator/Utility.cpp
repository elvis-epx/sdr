/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include <stdlib.h>
#include <string.h>
#include "Utility.h"

Dict::Dict()
{
	keys = 0;
	values = 0;
	len = 0;
}

Dict& Dict::operator=(Dict&& moved)
{
	this->keys = moved.keys;
	this->values = moved.values;
	this->len = moved.len;
	moved.keys = 0;
	moved.values = 0;
	moved.len = 0;
	return *this;
}

Dict& Dict::operator=(const Dict& model)
{
	
	for (int i = 0; i < len; ++i) {
		delete keys[i];
		delete values[i];
	}

	delete [] keys;
	delete [] values;
	keys = 0;
	values = 0;
	len = 0;

	keys = new Buffer*[model.len];
	values = new Buffer*[model.len];
	len = model.len;

	for (int i = 0; i < len; ++i) {
		keys[i] = new Buffer(*model.keys[i]);
		if (model.values[i]) {
			values[i] = new Buffer(*model.values[i]);
		} else {
			values[i] = 0;
		}
	}

	return *this;
}

Dict::~Dict()
{
	for (int i = 0; i < len; ++i) {
		delete keys[i];
		delete values[i];
	}
	delete keys;
	delete values;
	keys = 0;
	values = 0;
	len = 0;
}

Dict::Dict(Dict &&moved)
{
	this->keys = moved.keys;
	this->values = moved.values;
	this->len = moved.len;
	moved.keys = 0;
	moved.values = 0;
	moved.len = 0;
}

Dict::Dict(const Dict &model)
{
	keys = new Buffer*[model.len];
	values = new Buffer*[model.len];
	len = model.len;

	for (int i = 0; i < len; ++i) {
		keys[i] = new Buffer(*model.keys[i]);
		if (model.values[i]) {
			values[i] = new Buffer(*model.values[i]);
		} else {
			values[i] = 0;
		}
	}
}

int Dict::indexOf(const char* key) const
{
	for (int i = 0; i < len; ++i) {
		if (0 == strcmp(key, keys[i]->rbuf())) {
			return i;
		}
	}

	return -1;
}

bool Dict::has(const char* key) const
{
	return indexOf(key) != -1;
}

const char *Dict::get(const char *key) const
{
	int pos = indexOf(key);
	if (pos <= -1) {
		return 0;
	}
	if (!values[pos]) {
		return 0;
	}
	return values[pos]->rbuf();
}

bool Dict::put(const char *akey)
{
	return this->put(Buffer(akey), 0);
}

bool Dict::put(const Buffer &akey)
{
	return this->put(akey, 0);
}

bool Dict::put(const char *akey, const char *value)
{
	if (value) {
		return this->put(Buffer(akey), new Buffer(value));
	} else {
		return this->put(Buffer(akey), 0);
	}
}

bool Dict::put(const Buffer& akey, const Buffer* value)
{
	Buffer key = Buffer(akey);
	key.uppercase();

	int pos = indexOf(key.rbuf());
	bool ret = false;

	if (pos <= -1) {
		len += 1;
		Buffer **old_keys = keys;
		Buffer **old_values = values;
		keys = new Buffer*[len];
		values = new Buffer*[len];
		for (unsigned int i = 0; i < len - 1; ++i) {
			keys[i] = old_keys[i];
			values[i] = old_values[i];
		}
		delete old_keys;
		delete old_values;
		pos = len - 1;
		ret = true;
	} else {
		delete keys[pos];
		delete values[pos];
	}

	keys[pos] = new Buffer(key);
	if (value) {
		values[pos] = new Buffer(*value);
	} else {
		values[pos] = 0;
	}

	return ret;
}

void Dict::foreach(void* cargo, bool (*f)(const Buffer&, const Buffer*, void*)) const
{
	for (int i = 0; i < len; ++i) {
		if (! f(*keys[i], values[i], cargo)) {
			break;
		}
	}
}

int Dict::count() const
{
	return len;
}

Buffer::Buffer()
{
	this->len = 0;
	this->buf = 0;
}

Buffer::Buffer(int len)
{
	this->len = len;
	this->buf = (char*) calloc(len + 1, sizeof(char));
}

Buffer::Buffer(Buffer&& moved)
{
	this->len = moved.len;
	this->buf = moved.buf;
	moved.len = 0;
	moved.buf = 0;
}

Buffer::Buffer(const Buffer& model)
{
	this->len = model.len;
	this->buf = (char*) malloc(this->len + 1);
	if (model.buf) {
		memcpy(this->buf, model.buf, this->len);
	}
	this->buf[len] = 0;
}

Buffer& Buffer::operator=(Buffer&& moved)
{
	this->len = moved.len;
	this->buf = moved.buf;
	moved.len = 0;
	moved.buf = 0;
	return *this;
}

Buffer& Buffer::operator=(const Buffer& model)
{
	free(this->buf);
	this->buf = 0;

	this->len = model.len;
	this->buf = (char*) malloc(this->len + 1);
	if (model.buf) {
		memcpy(this->buf, model.buf, this->len);
	}
	this->buf[len] = 0;

	return *this;
}

void Buffer::append(const char *s)
{
	if (!s) {
		return;
	}

	unsigned int slen = strlen(s);
	this->buf = (char*) realloc(this->buf, this->len + slen);
	memcpy(this->buf + this->len, s, slen);

	this->len += slen;
	this->buf[this->len] = 0;
}

Buffer::~Buffer()
{
	free(this->buf);
	this->buf = 0;
}

Buffer::Buffer(const char *buf, int len)
{
	this->len = len;
	this->buf = (char*) malloc(len + 1);
	if (buf) {
		memcpy(this->buf, buf, len);
	}
	this->buf[len] = 0;
}

Buffer::Buffer(const char *s)
{
	this->len = strlen(s);
	this->buf = strdup(s);
}

const char* Buffer::rbuf() const
{
	return buf;
}

char* Buffer::wbuf()
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
