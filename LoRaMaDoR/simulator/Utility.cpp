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

bool Dict::put(const String& key, const String* value)
{	
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

int Dict::length() const
{
	return len;
}

Buffer::Buffer(int len)
{
	this->len = len;
	this->buf = (char*) calloc(len, sizeof(char));
}

Buffer::Buffer(const char *buf, int len)
{
	this->len = len;
	this->buf = (char*) malloc(len);
	memcpy(this->buf, buf, len);
	this->buf[len] = 0;
}

String Buffer::Str() const
{
	return String(this->buf);
}
