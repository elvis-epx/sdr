#include <Arduino.h>
#include <stdlib.h>
#include <Preferences.h>
#include "Buffer.h"

Preferences prefs;

unsigned long int arduino_millis()
{
	return millis();
}

long int arduino_random(long int min, long int max)
{
	return random(min, max);
}

void logs(const char* a, const char* b) {
	return;
}

void logi(const char* a, long int b) {
	return;
}

unsigned int arduino_nvram_id_load()
{
	prefs.begin("LoRaMaDoR");
	unsigned int id = prefs.getUInt("lastid");
	prefs.end();

	if (id <= 0 || id > 9999) {
		id = 1;
	}

	return id;
}

void arduino_nvram_id_save(unsigned int id)
{
	prefs.begin("LoRaMaDoR", false);
	prefs.putUInt("lastid", id);
	prefs.end();

}

Buffer arduino_nvram_callsign_load()
{
	Buffer callsign = "          ";
	prefs.begin("LoRaMaDoR");
	size_t len = prefs.getString("callsign", callsign.hot(), 10);
	prefs.end();

	if (!len) {
		callsign = "FIXMEE-1";
	}

	callsign.uppercase();
	return callsign;
}

void arduino_nvram_callsign_save(const Buffer &new_callsign)
{
	prefs.begin("LoRaMaDoR", false);
	prefs.putString("callsign", new_callsign.cold());
	prefs.end();
}
