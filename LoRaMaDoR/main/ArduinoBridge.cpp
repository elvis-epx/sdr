#include <Arduino.h>
#include <stdlib.h>
#include <Preferences.h>

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
	char *msg = new char[300];
	snprintf(msg, 300, "%s %s", a, b);
	Serial.println(msg);
	delete msg;
	// show_diag(msg);
}

void logi(const char* a, long int b) {
	return;
	char *msg = new char[300];
	snprintf(msg, 300, "%s %ld", a, b);
	Serial.println(msg);
	delete msg;
	// show_diag(msg);
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

char *arduino_nvram_callsign_load()
{
	char *callsign = malloc(11);
	prefs.begin("LoRaMaDoR");
	size_t len = prefs.getString("callsign", callsign, 10);
	callsign[len] = 0;
	prefs.end();

	if (!len) {
		strcpy(callsign, "FIXMEE-1");
	}

	return callsign;
}

void arduino_nvram_callsign_save(const char* new_callsign)
{
	prefs.begin("LoRaMaDoR", false);
	prefs.putString("callsign", new_callsign);
	prefs.end();
}
