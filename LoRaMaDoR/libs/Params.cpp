#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "Params.h"

static const char *naked = " n@ ";

static bool parse_symbol_param(const char *data, unsigned int len, Buffer& key, Buffer& value)
{
	if (! len) {
		return false;
	}

	unsigned int skey_len = 0;
	unsigned int svalue_len = 0;

	// find '=' separator, if exists
	const char *equal = (const char*) memchr(data, '=', len);

	if (! equal) {
		// naked key
		skey_len = len;
		svalue_len = 0;
	} else {
		// key=value, value may be empty
		skey_len = equal - data;
		svalue_len = len - skey_len - 1;
	}

	// check key name characters
	for (unsigned int i = 0; i < skey_len; ++i) {
		char c = data[i];
		if (c >= 'a' && c <= 'z') {
		} else if (c >= 'A' && c <= 'Z') {
		} else if (c >= '0' && c <= '9') {
		} else {
			return false;
		}
	}
	
	// check value characters, if there is a value
	if (equal) {
		for (unsigned int i = 0; i < svalue_len; ++i) {
			char c = equal[1 + i];
			if (strchr("= ,:<", c) || c == 0) {
				return false;
			}
		}
	}

	key = Buffer(data, skey_len);

	if (equal) {
		value = Buffer(equal + 1, svalue_len);
	} else {
		value = Buffer(naked);
	}

	return true;
}

static bool parse_ident_param(const char* s, unsigned int len, unsigned long int &ident)
{
	char *stop;
	ident = strtol(s, &stop, 10);
	if (ident <= 0) {
		return false;
	} else if (ident > 999999) {
		return false;
	} else if (len != (stop - s)) {
		return false;
	}

	char n[10];
	snprintf(n, 10, "%ld", ident);
	if (strlen(n) != len) {
		return false;
	}

	return true;
}

static bool parse_param(const char* data, unsigned int len,
		unsigned long int &ident, Buffer &key, Buffer &value)
{
	if (! len) {
		return false;
	}

	char c = data[0];

	if (c >= '0' && c <= '9') {
		return parse_ident_param(data, len, ident);
	} else if (c >= 'a' && c <= 'z') {
		ident = 0;
		return parse_symbol_param(data, len, key, value);
	} else if (c >= 'A' && c <= 'Z') {
		ident = 0;
		return parse_symbol_param(data, len, key, value);
	}

	return false;
}

static bool parse_params(const char *data, unsigned int len,
		unsigned long int &ident, Dict<Buffer> &params)
{
	ident = 0;
	params = Dict<Buffer>();

	while (len > 0) {
		unsigned int param_len;
		unsigned int advance_len;

		const char *comma = (const char*) memchr(data, ',', len);
		if (! comma) {
			// last, or only, param
			param_len = len;
			advance_len = len;
		} else {
			param_len = comma - data;
			advance_len = param_len + 1;
		}

		if (! param_len) {
			return false;
		}

		unsigned long int tident = 0;
		Buffer key;
		Buffer value;

		if (! parse_param(data, param_len, tident, key, value)) {
			return false;
		}
		if (tident) {
			// parameter is ident
			ident = tident;
		} else {
			// parameter is key=value or naked key
			params.put(key, value); // uppers key case for us
		}

		data += advance_len;
		len -= advance_len;
	}

	return true;
}

Params::Params()
{
	_ident = 0;
	valid = true;
}

Params::Params(Buffer b)
{
	valid = parse_params(b.cold(), b.length(), _ident, items);
}

Buffer Params::serialized() const
{
	Buffer buf = Buffer::sprintf("%ld", _ident);

	const Vector<Buffer>& keys = items.keys();
	for (unsigned int i = 0; i < keys.size(); ++i) {
		const Buffer& key = keys[i];
		const Buffer& value = items[key];
		buf.append(',');
		buf.append_str(key);
		if (! value.str_equal(naked)) {
			buf.append('=');
			buf.append_str(value);
		}
	}

	return buf;
}

bool Params::is_valid_with_ident() const
{
	return valid && _ident;
}

bool Params::is_valid_without_ident() const
{
	return valid;
}

unsigned long int Params::ident() const
{
	return _ident;
}

unsigned int Params::count() const
{
	return items.count();
}

Buffer Params::get(const char *key) const
{
	return items.get(key);
}

bool Params::has(const char *key) const
{
	return items.has(key);
}

void Params::put(const char *key, const Buffer& value)
{
	items.put(key, value);
}

void Params::put_naked(const char *key)
{
	items.put(key, naked);
}

bool Params::is_key_naked(const char* key) const
{
	return items.has(key) && items.get(key).str_equal(naked);
}

void Params::set_ident(unsigned long int new_ident)
{
	_ident = new_ident;
}
