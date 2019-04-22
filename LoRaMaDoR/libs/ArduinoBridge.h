// Functions implemented in Arduino or faked in Unix

#ifndef __ARDUINO_BRIDGE
#define __ARDUINO_BRIDGE
unsigned long int arduino_millis();
long int arduino_random(long int min, long int max);
void logs(const char*, const char*);
void logi(const char*, long int);
#endif
