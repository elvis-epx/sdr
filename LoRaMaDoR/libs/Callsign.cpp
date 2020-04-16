#include "Callsign.h"
#include <string.h>

Callsign::Callsign()
{
	valid = false;
}

Callsign::Callsign(Buffer c)
{
	c.uppercase();
	c.strip();
	if (! check(c)) {
		valid = false;
		return;
	}
	buffer = c;
	valid = true;
}

bool Callsign::equal(const Buffer& other) const
{
	return valid && buffer.str_equal(other);
}

bool Callsign::equal(const Callsign& other) const
{
	
	return valid && other.valid && buffer.str_equal(other.buffer);
}

bool Callsign::is_localhost() const
{
	return buffer.str_equal("QL");
}

bool Callsign::isQ() const
{
	return buffer.charAt(0) == 'Q';
}

Buffer Callsign::buf() const
{
	return buffer;
}

bool Callsign::is_valid() const
{
	return valid;
}

bool Callsign::check(const Buffer &sbuf)
{
	unsigned int length = sbuf.length();
	const char *s = sbuf.cold();

	if (length < 2) {
		return false;
	} else if (length == 2) {
		char c0 = s[0];
		char c1 = s[1];
		if (c0 != 'Q') {
			return false;
		}
		if (c1 < 'A' || c1 > 'Z') {
			return false;
		}
	} else {
		char c0 = s[0];
		if (c0 == 'Q'|| c0 < 'A' || c0 > 'Z') {
			return false;
		}

		const char *ssid_delim = strchr(s, '-');
		unsigned int prefix_length;

		if (ssid_delim) {
			const char *ssid = ssid_delim + 1;
			prefix_length = ssid_delim - s;
			int ssid_length = length - 1 - prefix_length;
			if (ssid_length <= 0 || ssid_length > 2) {
				return false;
			}
			bool sig = false;
			for (int i = 0; i < ssid_length; ++i) {
				char c = ssid[i];
				if (c < '0' || c > '9') {
					return false;
				}
				if (c != '0') {
					// found significant digit
					sig = true;
				} else if (! sig) {
					// non-significant 0
					return false;
				}
			}
		} else {
			prefix_length = length;
		}

		if (prefix_length > 7 || prefix_length < 4) {
			return false;
		}
		for (unsigned int i = 1; i < prefix_length; ++i) {
			char c = s[i];
			if (c >= '0' && c <= '9') {
			} else if (c >= 'A' && c <= 'Z') {
			} else {
				return false;
			}
		}
	}

	return true;
}

