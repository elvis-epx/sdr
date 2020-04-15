#include "Packet.h"
#include "Network.h"

const char *my_prefix = "PU5EPX-1";
const long int AVG_BEACON_TIME = 30000;

Ptr<Network> Net;

void setup()
{
	Serial.begin(115200);
	oled_init();
	oled_show("setup", "", "", "");
	Net = net(my_prefix);
	oled_show("net ok", "", "", "");
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
	Net->run_tasks(millis());
}

void send_message()
{
	// oled_show("send_message()");
	Net->send("QC", Params(), "LoRaMaDoR 73!");
	// oled_show("send_message() ok");
}

void app_recv(Ptr<Packet> pkt)
{
	char *msg = new char[400];
	char *msga = new char[80];
	char *msgb = new char[80];
	snprintf(msg, 400, "RSSI %d %s < %s id %ld params %s msg %s",
				pkt->rssi(), pkt->to(), pkt->from(),
				pkt->ident(), pkt->sparams(),
				pkt->msg().cold());
	Serial.println(msg);
	snprintf(msga, 80, "%s < %s  id %ld", pkt->to(), pkt->from(), pkt->ident());
	snprintf(msgb, 80, "RSSI %d params %s", pkt->rssi(), pkt->sparams());
	oled_show(msga, msgb, pkt->msg().cold(), "");
	delete msg, msga, msgb;
}
