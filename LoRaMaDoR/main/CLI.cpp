#include <Arduino.h>
#include "Buffer.h"
#include "ArduinoBridge.h"

void logs(const char* a, const char* b) {
	Buffer msg = Buffer::sprintf("%s %s", a, b);
	cli_showpkt(msg);
}

void logi(const char* a, long int b) {
	Buffer msg = Buffer::sprintf("%s %ld", a, b);
	cli_showpkt(msg);
}

void app_recv(Ptr<Packet> pkt)
{
	Buffer msg = Buffer::sprintf("%s < %s %s\nid %ld params %s RSSI %d",
				pkt->to(), pkt->from(), pkt->msg().cold(),
				pkt->ident(), pkt->sparams(), pkt->rssi());
	cli_showpkt(msg);
	Buffer msga = Buffer::sprintf("%s < %s", pkt->to(), pkt->from());
	Buffer msgb = Buffer::sprintf("id %ld rssi %d", pkt->ident(), pkt->rssi());
	Buffer msgc = Buffer::sprintf("p %s", pkt->sparams());
	oled_show(msga.cold(), pkt->msg().cold(), msgb.cold(), msgc.cold());
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

void cli_showpkt(const Buffer &msg)
{
	Serial.println();
	Serial.println(msg.cold());
	Serial.print(cli_buf.cold());
}

void cli_parse(Buffer cmd)
{
	cmd.lstrip();
	if (cmd.charAt(0) == '!') {
		cmd.cut(1);
		cli_parse_meta(cmd);
	} else {
		Serial.println("FIXME parse packet");
	}
}

void cli_parse_meta(Buffer cmd)
{
	cmd.strip();
	if (cmd.strncmp("callsign ", 9) == 0) {
		cmd.cut(9);
		cli_parse_callsign(cmd);
	} else if (cmd.strncmp("callsign", 8) == 0 && cmd.length() == 8) {
		cli_parse_callsign("");
	} else {
		Serial.print("Unknown cmd: ");
		Serial.println(cmd.cold());
	}
}

void cli_parse_callsign(Buffer callsign)
{
	callsign.strip();
	callsign.uppercase();

	if (callsign.empty()) {
		Serial.print("Callsign is ");
		Serial.println(Net->callsign().cold());
		return;
	}

	if (! Packet::check_callsign(callsign)) {
		Serial.print("Invalid callsign: ");
		Serial.println(callsign.cold());
		return;
	}
	if (callsign.charAt(0) == 'Q') {
		Serial.print("Invalid Q callsign: ");
		Serial.println(callsign.cold());
		return;
	}
	
	arduino_nvram_callsign_save(callsign);
	Serial.println("Callsign saved, restarting...");
	ESP.restart();
}
