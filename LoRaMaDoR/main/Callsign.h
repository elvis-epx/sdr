#ifndef __CALLSIGN_H
#define __CALLSIGN_H

#include "Buffer.h"

class Callsign
{
public:
	Callsign();
	Callsign(Buffer);
	Buffer buf() const;
	bool is_valid() const;
	bool isQ() const;
	bool is_localhost() const;
	bool equal(const Buffer&) const;
	bool equal(const Callsign&) const;
private:
	static bool check(const Buffer&);
	Buffer buffer;
	bool valid;
};

#endif
