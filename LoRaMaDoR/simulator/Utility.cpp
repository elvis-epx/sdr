/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#include <stdlib.h>
#include "Utility.h"

Dict::Dict()
{
	keys = (String**) malloc(0);
	values = (String**) malloc(0);
	len = 0;
}

Dict& Dict::operator=(const Dict& model)
{
	
	for (int i = 0; i < len; ++i) {
		delete keys[i];
		delete values[i];
	}

	free(keys);
	free(values);
	keys = 0;
	values = 0;
	len = 0;

	keys = (String**) calloc(model.len, sizeof(String*));
	values = (String**) calloc(model.len, sizeof(String*));
	len = model.len;

	for (int i = 0; i < len; ++i) {
		keys[i] = new String(*model.keys[i]);
		if (model.values[i]) {
			values[i] = new String(*model.values[i]);
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

	free(keys);
	free(values);
	keys = 0;
	values = 0;
	len = 0;
}

Dict::Dict(const Dict &model)
{
	keys = (String**) calloc(model.len, sizeof(String*));
	values = (String**) calloc(model.len, sizeof(String*));
	len = model.len;

	for (int i = 0; i < len; ++i) {
		keys[i] = new String(*model.keys[i]);
		if (model.values[i]) {
			values[i] = new String(*model.values[i]);
		}
	}
}

int Dict::indexOf(const String &key) const
{
	for (int i = 0; i < len; ++i) {
		if (key == *keys[i]) {
			return i;
		}
	}

	return -1;
}

bool Dict::has(const String& key) const
{
	return indexOf(key) != -1;
}

const String *Dict::get(const String& key) const
{
	int pos = indexOf(key);
	if (pos <= -1) {
		return 0;
	}
	return values[pos];
}

bool Dict::put(const String& key, const String& value)
{
	return put(key, &value);
}

bool Dict::put(const String& key)
{
	return put(key, 0);
}

bool Dict::put(const String& akey, const String* value)
{
	String key = akey;
	key.toUpperCase();

	int pos = indexOf(key);
	bool ret = false;

	if (pos <= -1) {
		len += 1;
		keys = (String**) realloc(keys, len * sizeof(String*));
		values = (String**) realloc(values, len * sizeof(String*));
		pos = len - 1;
		ret = true;
	} else {
		delete keys[pos];
		delete values[pos];
	}

	keys[pos] = new String(key);
	if (value) {
		values[pos] = new String(*value);
	} else {
		values[pos] = 0;
	}

	return ret;
}

void Dict::foreach(void* cargo, bool (*f)(const String&, const String*, void*)) const
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

Buffer::Buffer(int len)
{
	this->len = len;
	this->buf = (char*) calloc(len + 1, sizeof(char));
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

Buffer::Buffer(const String &s)
{
	this->len = s.length();
	this->buf = (char*) malloc(s.length() + 1);
	s.toCharArray(this->buf, s.length() + 1);
}

String Buffer::Str() const
{
	return String(this->buf);
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
