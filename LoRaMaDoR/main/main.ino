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
	Buffer callsign = arduino_nvram_callsign_load();
	Net = net(callsign);

	oled_show("Net configured", callsign.cold(), "", "");
	Serial.print(callsign.cold());
	Serial.println(" ready");
	Serial.println();
}

long nextSendTime = millis() + 5000;

void loop()
{
	if (millis() > nextSendTime) {
		send_message();
		long int next = random(AVG_BEACON_TIME / 2,
				AVG_BEACON_TIME * 3 / 2);
		nextSendTime = millis() + next;
		return;
	}

	while (Serial.available() > 0) {
		cli_type(Serial.read());
	}

	Net->run_tasks(millis());
}
