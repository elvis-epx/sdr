#include "SSD1306.h"
#include "Packet.h"
#include "Network.h"

const char *my_prefix = "PU5EPX-1";
const long int AVG_BEACON_TIME = 30000;

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

char *lines[5] = {0, 0, 0, 0, 0};
int linecount = 0;

void show_diag(const char *msg)
{
	if (linecount < 5) {
		lines[linecount++] = strdup(msg);
	} else {
		free(lines[0]);
		lines[0] = lines[1];
		lines[1] = lines[2];
		lines[2] = lines[3];
		lines[3] = lines[4];
		lines[4] = strdup(msg);
	}
	display.clear();
	display.drawStringMaxWidth(0, 0, 80, lines[0]);
	if (lines[1]) display.drawStringMaxWidth(0, 12, 80, lines[1]);
	if (lines[2]) display.drawStringMaxWidth(0, 24, 80, lines[2]);
	if (lines[3]) display.drawStringMaxWidth(0, 36, 80, lines[3]);
	if (lines[4]) display.drawStringMaxWidth(0, 48, 80, lines[4]);
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

long nextSendTime = millis() + 1000;

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
	Net->send("QC", Params(), "LoRaMaDoR 73!");
}

void app_recv(Ptr<Packet> pkt)
{
  char msg[300];
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
  char msg[300];
  snprintf(msg, sizeof(msg), "%s %s", a, b);
  show_diag(msg);
}

void logi(const char* a, long int b) {
  char msg[300];
  snprintf(msg, sizeof(msg), "%s %ld", a, b);
  show_diag(msg);
}
