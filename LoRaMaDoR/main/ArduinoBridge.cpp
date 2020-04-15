unsigned long int arduino_millis()
{
	return millis();
}

long int arduino_random(long int min, long int max)
{
	return random(min, max);
}

void logs(const char* a, const char* b) {
	return;
	char *msg = new char[300];
	snprintf(msg, 300, "%s %s", a, b);
	Serial.println(msg);
	delete msg;
	// show_diag(msg);
}

void logi(const char* a, long int b) {
	return;
	char *msg = new char[300];
	snprintf(msg, 300, "%s %ld", a, b);
	Serial.println(msg);
	delete msg;
	// show_diag(msg);
}
