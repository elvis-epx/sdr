#ifndef __CALLSIGN_H
#define __CALLSIGN_H

#include "Buffer.h"

class Callsign
{
public:
	Callsign();
	Callsign(const Buffer&);
	Buffer buf() const;
	bool is_valid() const;
	static bool check_callsign(const Buffer&);
private:
	Buffer buffer;
	bool valid;
};

#endif
