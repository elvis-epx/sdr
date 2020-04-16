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
				pkt->to().buf().cold(), pkt->from().buf().cold(), pkt->msg().cold(),
				pkt->params().serialized().cold(), pkt->rssi());
	cli_print(msg);
	Buffer msga = Buffer::sprintf("%s < %s", pkt->to().buf().cold(), pkt->from().buf().cold());
	Buffer msgb = Buffer::sprintf("id %ld rssi %d", pkt->params().ident(), pkt->rssi());
	Buffer msgc = Buffer::sprintf("p %s", pkt->params().serialized().cold());
	oled_show(msga.cold(), pkt->msg().cold(), msgb.cold(), msgc.cold());
}

void cli_parse_callsign(const Buffer &candidate)
{
	if (candidate.empty()) {
		Serial.print("Callsign is ");
		Serial.println(Net->me().buf().cold());
		return;
	}
	
	if (candidate.charAt(0) == 'Q') {
		Serial.print("Invalid Q callsign: ");
		Serial.println(candidate.cold());
		return;
	}

	Callsign callsign(candidate);

	if (! callsign.is_valid()) {
		Serial.print("Invalid callsign: ");
		Serial.println(candidate.cold());
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

	Buffer cdest;
	Buffer sparams = "";
	int sep = preamble.indexOf(':');
	if (sep < 0) {
		cdest = preamble;
	} else {
		cdest = preamble.substr(0, sep);
		sparams = preamble.substr(sep + 1);
	}

	Callsign dest(cdest);

	if (! dest.is_valid()) {
		Serial.print("Invalid destination: ");
		Serial.println(cdest.cold());
		return;
	}

	unsigned long int dummy;
	Params params(sparams);
	if (! params.is_valid_without_ident()) {
		Serial.print("Invalid params: ");
		Serial.println(sparams.cold());
		return;
	}

	Net->send(dest, params, payload);
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
