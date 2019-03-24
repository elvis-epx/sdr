/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include <stdlib.h>
#include <string.h>
#include "Utility.h"

Dict::Dict()
{
	keys = (char**) malloc(0);
	values = (char**) malloc(0);
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
		free(keys[i]);
		free(values[i]);
	}

	free(keys);
	free(values);
	keys = 0;
	values = 0;
	len = 0;

	keys = (char**) calloc(model.len, sizeof(char*));
	values = (char**) calloc(model.len, sizeof(char*));
	len = model.len;

	for (int i = 0; i < len; ++i) {
		keys[i] = strdup(model.keys[i]);
		if (model.values[i]) {
			values[i] = strdup(model.values[i]);
		}
	}

	return *this;
}

Dict::~Dict()
{
	for (int i = 0; i < len; ++i) {
		free(keys[i]);
		free(values[i]);
	}

	free(keys);
	free(values);
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
	keys = (char**) calloc(model.len, sizeof(char*));
	values = (char**) calloc(model.len, sizeof(char*));
	len = model.len;

	for (int i = 0; i < len; ++i) {
		keys[i] = strdup(model.keys[i]);
		if (model.values[i]) {
			values[i] = strdup(model.values[i]);
		}
	}
}

int Dict::indexOf(const char* key) const
{
	for (int i = 0; i < len; ++i) {
		if (0 == strcmp(key, keys[i])) {
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
	return values[pos];
}

bool Dict::put(const char *akey)
{
	return this->put(akey, 0);
}

bool Dict::put(const char *akey, const char *value)
{
	char *key = strdup(akey);
	int n = strlen(key);
	for (int i = 0; i < n; ++i) {
		if (key[i] >= 'a' && key[i] <= 'z') {
			key[i] += 'A' - 'a';
		}
	}

	int pos = indexOf(key);
	bool ret = false;

	if (pos <= -1) {
		len += 1;
		keys = (char**) realloc(keys, len * sizeof(char*));
		values = (char**) realloc(values, len * sizeof(char*));
		pos = len - 1;
		ret = true;
	} else {
		free(keys[pos]);
		free(values[pos]);
	}

	keys[pos] = key;
	if (value) {
		values[pos] = strdup(value);
	} else {
		values[pos] = 0;
	}

	return ret;
}

void Dict::foreach(void* cargo, bool (*f)(const char*, const char*, void*)) const
{
	for (int i = 0; i < len; ++i) {
		if (! f(keys[i], values[i], cargo)) {
			break;
		}
	}
}

int Dict::count() const
{
	return len;
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

void uppercase(char *s)
{
	while (*s) {
		if (*s >= 'a' && *s <= 'z') {
			*s += 'A' - 'a';
		}
		++s;
	}
}
