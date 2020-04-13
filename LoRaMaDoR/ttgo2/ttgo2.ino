#include "SSD1306.h"
#include "Packet.h"
#include "Network.h"

const char *my_prefix = "PU5EPX-2";
const long int AVG_BEACON_TIME = 5000;

SSD1306 display(0x3c, 4, 15);

void display_init()
{
  pinMode(16, OUTPUT);
  pinMode(25, OUTPUT);

  digitalWrite(16, LOW); // reset
  delay(50);
  digitalWrite(16, HIGH); // keep high while operating display

  display.init();
  display.flipScreenVertically();
  display.setFont(ArialMT_Plain_10);
  display.setTextAlignment(TEXT_ALIGN_LEFT);
}

void show_diag(const char *msg)
{
	char ms[20];
	sprintf(ms, "%ld", millis());
	display.clear();
	display.drawString(0, 0, msg);
	display.drawString(0, 48, ms);
	display.display();
	Serial.println(msg);
}

Ptr<Network> Net;

void setup()
{
  Serial.begin(115200);
  display_init();
  show_diag("setup");
  Net = net(my_prefix);
  show_diag("net ok");
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
	show_diag("send_message()");
	Net->send("QC", Params(), "LoRaMaDoR 73!");
	show_diag("send_message() ok");
}

char msg[300];

void app_recv(Ptr<Packet> pkt)
{
	show_diag("recv");
	snprintf(msg, sizeof(msg), "RSSI %d %s < %s id %ld params %s msg %s",
           pkt->rssi(),	pkt->to(), pkt->from(),
           pkt->ident(), pkt->sparams(), pkt->msg().cold());
  show_diag(msg);
}

unsigned long int arduino_millis()
{
	return millis();
}

long int arduino_random(long int min, long int max)
{
	return random(min, max);
}

void logs(const char* a, const char* b) {
  snprintf(msg, sizeof(msg), "%s %s", a, b);
  Serial.println(msg);
}

void logi(const char* a, long int b) {
  snprintf(msg, sizeof(msg), "%s %ld", a, b);
  Serial.println(msg);
}
