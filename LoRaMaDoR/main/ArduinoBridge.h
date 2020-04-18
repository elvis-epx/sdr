// Functions implemented in Arduino or faked in Unix

#ifndef __ARDUINO_BRIDGE
#define __ARDUINO_BRIDGE
#include "Pointer.h"
#include "Packet.h"
#include "Callsign.h"

unsigned long int arduino_millis();
long int arduino_random(long int min, long int max);
void logs(const char*, const char*);
void logi(const char*, long int);
void app_recv(Ptr<Packet>);
unsigned int arduino_nvram_id_load();
void arduino_nvram_id_save(unsigned int);
Callsign arduino_nvram_callsign_load();
void arduino_nvram_callsign_save(const Callsign&);

#endif
