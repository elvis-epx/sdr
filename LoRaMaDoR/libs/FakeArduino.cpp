#include <sys/time.h>

static struct timeval tm_first;
static bool virgin = true;

unsigned long int arduino_millis()
{
	if (virgin) {
		gettimeofday(&tm_first, 0);
		virgin = false;
	}
	struct timeval tm;
	gettimeofday(&tm, 0);
	return ((tm.tv_sec * 1000000 + tm.tv_usec)
		- (tm_first.tv_sec * 1000000 + tm_first.tv_usec)) / 1000;
}
