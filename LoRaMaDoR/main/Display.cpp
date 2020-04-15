#include "Display.h"
#include "SSD1306.h"

SSD1306 display(0x3c, 4, 15);

void oled_init()
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

void oled_show(const char *ma, const char *mb, const char *mc, const char *md)
{
	char ms[20];
	sprintf(ms, "%ld", millis());
	display.clear();
	display.drawString(0, 0, ma);
	display.drawString(0, 12, mb);
	display.drawString(0, 24, mc);
	display.drawString(0, 36, md);
	display.drawString(0, 48, ms);
	display.display();
}
