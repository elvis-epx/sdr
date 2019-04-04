// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#include <stdio.h>
#include "Log.h"

void logs(const char* s1, const char* s2)
{
	printf("%s %s\n", s1, s2);
}

void logi(const char* s1, long int s2)
{
	printf("%s %ld\n", s1, s2);
}
