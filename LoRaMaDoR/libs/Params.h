#ifndef __PARAMS_H
#define __PARAMS_H

#include "Buffer.h"
#include "Dict.h"

class Params
{
public:
	Params();
	Params(Buffer);
	Buffer serialized() const;
	bool is_valid_with_ident() const;
	bool is_valid_without_ident() const;
	unsigned long int ident() const;
	unsigned int count() const;
	Buffer get(const char *) const;
	bool has(const char *) const;
	void put(const char *, const Buffer&);
	void put_naked(const char *);
	bool is_key_naked(const char *) const;
	void set_ident(unsigned long int);
private:
	Dict<Buffer> items;
	unsigned long int _ident;
	bool valid;
};

#endif
