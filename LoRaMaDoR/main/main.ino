#include "Packet.h"
#include "Network.h"
#include "Display.h"
#include "ArduinoBridge.h"

const long int AVG_BEACON_TIME = 30000;

Ptr<Network> Net;

void setup()
{
	Serial.begin(115200);
	oled_init();
	oled_show("setup", "", "", "");
	char *callsign = arduino_nvram_callsign_load();
	Net = net(callsign);
	oled_show("net ok", callsign, "", "");
	Serial.print(callsign);
	Serial.println(" ready");
	Serial.println();
	free(callsign);
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
	/*
	while (Serial.available() > 0) {
		cli_type(Serial.read());
	}
	*/
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
	Buffer msg = Buffer::sprintf("RSSI %d %s < %s id %ld params %s msg %s",
				pkt->rssi(), pkt->to(), pkt->from(),
				pkt->ident(), pkt->sparams(),
				pkt->msg().cold());
	cli_showpkt(msg);
	Buffer msga = Buffer::sprintf("%s < %s", pkt->to(), pkt->from());
	Buffer msgb = Buffer::sprintf("id %ld rssi %d", pkt->ident(), pkt->rssi());
	Buffer msgc = Buffer::sprintf("p %s", pkt->sparams());
	oled_show(msga.cold(), msgb.cold(), msgc.cold(), pkt->msg().cold());
}

Buffer cli_buf;

void cli_type(char c) {
	if (c == 13) {
		cli_enter();
	} else if (c == 8 || c == 127) {
		if (! cli_buf.empty()) {
			cli_buf.cut(-1);
			Serial.print((char) 8);
			Serial.print(' ');
			Serial.print((char) 8);
		}
	} else if (cli_buf.length() > 500) {
		return;
	} else {
		cli_buf.append(c);
		Serial.print(c);
	}
}

void cli_enter() {
	Serial.println();
	if (cli_buf.empty()) {
		return;
	}
	// Serial.print("Typed: ");
	// Serial.println(cli_buffer);
	cli_parse(cli_buf);
	cli_buf = "";
}

void cli_showpkt(const Buffer &msg) {
	Serial.println();
	Serial.println(msg.cold());
	Serial.print(cli_buf.cold());
}

void cli_parse(Buffer cmd)
{
	int sp = cmd.indexOf(' ');
	if (sp >= 0) {
		cmd.cut(sp);
	}
	
	if (cmd.charAt(0) == '!') {
		cmd.cut(1);
		cli_parse_meta(cmd);
	} else {
		Serial.println("FIXME parse packet");
	}
}

void cli_parse_meta(Buffer cmd)
{
	if (cmd.strncmp("!callsign ", 10) == 0) {
		cmd.cut(10);
		cli_parse_callsign(cmd);
	} else {
		Serial.println("Unknown cmd");
	}
}

void cli_parse_callsign(Buffer callsign)
{
	callsign.uppercase();
	while (callsign.charAt(-1) == ' ') {
		callsign.cut(-1);
	}
	
	if (! Packet::check_callsign(callsign)) {
		Serial.println("Invalid callsign");
		return;
	}
	if (callsign.charAt(0) == 'Q') {
		Serial.println("Invalid Q callsign");
		return;
	}
	
	arduino_nvram_callsign_save(callsign);
	Serial.println("Callsign saved, restarting...");
	ESP.restart();
}
