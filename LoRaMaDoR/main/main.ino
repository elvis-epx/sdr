#include "Packet.h"
#include "Network.h"
#include "Display.h"
#include "ArduinoBridge.h"
#include "CLI.h"

const long int AVG_BEACON_TIME = 30000;

Ptr<Network> Net;

void setup()
{
	Serial.begin(115200);
	oled_init();

	oled_show("Starting...", "", "", "");
	Callsign cs = arduino_nvram_callsign_load();
	Net = Ptr<Network>(new Network(cs));
	oled_show("Net configured", cs.buf().cold(), "", "");
	Serial.print(cs.buf().cold());
	Serial.println(" ready");
	Serial.println();
}

void loop()
{
	while (Serial.available() > 0) {
		cli_type(Serial.read());
	}

	Net->run_tasks(millis());
}
