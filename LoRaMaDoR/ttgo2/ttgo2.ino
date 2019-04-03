#include "SSD1306.h"
#include "Packet.h"
#include "Radio.h"

// use button to toogle this.
const bool SEND_BEACON = true;
const bool RECEIVER = true;
const long int AVG_BEACON_TIME = 10000;

const char *my_prefix = "PU5EPX-2";

long int ident = 0; 
long nextSendTime = millis() + 1000;

int recv_pcount = 0;
int recv_dcount = 0;

SSD1306 display(0x3c, 4, 15);

void display_init()
{
	pinMode(16,OUTPUT);
	pinMode(25,OUTPUT);
	
	digitalWrite(16, LOW); // reset
	delay(50); 
	digitalWrite(16, HIGH); // keep high while operating display

	display.init();
	display.flipScreenVertically();
	display.setFont(ArialMT_Plain_10);
	display.setTextAlignment(TEXT_ALIGN_LEFT);
}

void show_diag(const char *error)
{
	display.clear();
	display.drawString(0, 0, error);
	display.display();

	Serial.println(error);
}

void setup()
{
	Serial.begin(9600);
	display_init();

	if (! setup_lora()) {
		show_diag("Starting LoRa failed!");
		while (1);
	}
	show_diag("LoRa ok");
	if (RECEIVER) {
		lora_rx(onReceive);
	}
}

void loop()
{
	if (SEND_BEACON) {
		if (millis() > nextSendTime) {
			send_message();
			long int next = random(AVG_BEACON_TIME / 2,
						AVG_BEACON_TIME * 3 / 2);
			nextSendTime = millis() + next;
			return;
		}
	}
	if (recv_pcount > recv_dcount) {
		recv_dcount = recv_pcount;
		recv_show();
	}
}

void show_sent(unsigned long int ident, unsigned int length, long int tx_time)
{
	char msg[50];
	snprintf(msg, sizeof(msg), "< %s #%ld, %u octets in %ldms", my_prefix, ident, length, tx_time);
	Serial.println(msg);

	display.clear();
	display.drawString(0, 0, String(my_prefix) + " sent #" + String(ident));
	display.drawString(0, 10, String(length) + " bytes in " + String(tx_time) + "ms");
	display.display();
}

void send_message()
{
	ident %= 999;
	++ident;
	Buffer msg = "LoRaMaDoR 73.";
	Packet p = Packet("QB", my_prefix, ident, Params(), msg);
	Buffer encoded = p.encode_l2();
	long int tx_time = lora_tx(encoded);
	show_sent(ident, encoded.length(), tx_time);
}

int recv_rssi;
String recv_from;
String recv_to;
unsigned long int recv_ident;
String recv_params;
String recv_msg;

// interrupt context, don't do too much here
void onReceive(const char *recv_area, unsigned int plen, int rssi)  
{
	recv_rssi = rssi;
	++recv_pcount;
	Ptr<Packet> p = Packet::decode_l2(recv_area, plen);
	if (!p) {
		recv_from = "";
		recv_to = "";
		recv_ident = 0;
		recv_params = "";
		recv_msg = ">>> Corrupted " + String(Packet::get_decode_error());
		return;
	}

	recv_from = p->from();
	recv_to = p->to();
	recv_ident = p->ident();
	recv_params = p->sparams();
	recv_msg = p->msg().cold();
}

void recv_show()
{
	char msg[300];
	snprintf(msg, sizeof(msg), "> #%ld RSSI %d %s < %s id %ld param %s msg %s",
		recv_pcount, recv_rssi,	recv_to.c_str(), recv_from.c_str(),
		recv_ident, recv_params.c_str(), recv_msg.c_str());
	Serial.println(msg);

	display.clear();
	display.drawString(0, 0, "Recv #" + String(recv_pcount) + " RSSI " + String(recv_rssi)); 
	display.drawString(0, 12, recv_to + " < " + recv_from);
	display.drawString(0, 24, "Ident " + String(recv_ident));
	display.drawString(0, 36, "Params " + recv_params);
	display.drawStringMaxWidth(0 , 48, 80, recv_msg); 
	display.display();
}
