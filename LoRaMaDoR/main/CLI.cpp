#include <Arduino.h>
#include "Buffer.h"
#include "ArduinoBridge.h"
#include "Display.h"
#include "Network.h"
#include "CLI.h"

extern Ptr<Network> Net;
bool debug = false;

void logs(const char* a, const char* b) {
	if (!debug) return;
	Buffer msg = Buffer::sprintf("%s %s", a, b);
	cli_print(msg);
}

void logi(const char* a, long int b) {
	if (!debug) return;
	Buffer msg = Buffer::sprintf("%s %ld", a, b);
	cli_print(msg);
}

void app_recv(Ptr<Packet> pkt)
{
	Buffer msg = Buffer::sprintf("%s < %s %s\n\r(%s rssi %d)",
				pkt->to(), pkt->from(), pkt->msg().cold(),
				pkt->sparams(), pkt->rssi());
	cli_print(msg);
	Buffer msga = Buffer::sprintf("%s < %s", pkt->to(), pkt->from());
	Buffer msgb = Buffer::sprintf("id %ld rssi %d", pkt->ident(), pkt->rssi());
	Buffer msgc = Buffer::sprintf("p %s", pkt->sparams());
	oled_show(msga.cold(), pkt->msg().cold(), msgb.cold(), msgc.cold());
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

void cli_parse_meta(Buffer cmd)
{
	cmd.strip();
	if (cmd.strncmp("callsign ", 9) == 0) {
		cmd.cut(9);
		cli_parse_callsign(cmd);
	} else if (cmd.strncmp("debug", 5) == 0 && cmd.length() == 5) {
		Serial.println("Debug on.");
		debug = true;
	} else if (cmd.strncmp("nodebug", 7) == 0 && cmd.length() == 7) {
		Serial.println("Debug off.");
		debug = false;
	} else if (cmd.strncmp("callsign", 8) == 0 && cmd.length() == 8) {
		cli_parse_callsign("");
	} else {
		Serial.print("Unknown cmd: ");
		Serial.println(cmd.cold());
	}
}

void cli_parse_packet(Buffer cmd)
{
	Buffer preamble;
	Buffer payload = "";
	int sp = cmd.indexOf(' ');
	if (sp < 0) {
		preamble = cmd;
	} else {
		preamble = cmd.substr(0, sp);
		payload = cmd.substr(sp + 1);
	}

	Buffer dest;
	Buffer sparams = "";
	int sep = preamble.indexOf(':');
	if (sep < 0) {
		dest = preamble;
	} else {
		dest = preamble.substr(0, sep);
		sparams = preamble.substr(sep + 1);
	}
	dest.strip();
	dest.uppercase();

	if (! Packet::check_callsign(dest)) {
		Serial.print("Invalid destination: ");
		Serial.println(dest.cold());
		return;
	}

	unsigned long int dummy;
	Params params;
	if (! Packet::parse_params_cli(sparams, params)) {
		Serial.print("Invalid params: ");
		Serial.println(sparams.cold());
		return;
	}

	Net->send(dest.cold(), params, payload);
}

void cli_parse(Buffer cmd)
{
	cmd.lstrip();
	if (cmd.charAt(0) == '!') {
		cmd.cut(1);
		cli_parse_meta(cmd);
	} else {
		cli_parse_packet(cmd);
	}
}

Buffer cli_buf;

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

void cli_print(const Buffer &msg)
{
	Serial.println();
	Serial.println(msg.cold());
	Serial.print(cli_buf.cold());
}
