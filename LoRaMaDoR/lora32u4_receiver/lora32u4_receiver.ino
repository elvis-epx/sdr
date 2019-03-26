#include <SPI.h>
#include <LoRa.h>
#include <RS-FEC.h>

// uncomment the section corresponding to your board
// BSFrance 2017 contact@bsrance.fr 

// NB : on this library with Atmega32u4 IRQ handling may not work

//  //LoR32u4 433MHz V1.0 (white board)
//  #define SCK     15
//  #define MISO    14
//  #define MOSI    16
//  #define SS      1
//  #define RST     4
//  #define DI0     7
//  #define BAND    433E6 
//  #define PABOOST true

//  //LoR32u4 433MHz V1.2 (white board)
//  #define SCK     15
//  #define MISO    14
//  #define MOSI    16
//  #define SS      8
//  #define RST     4
//  #define DI0     7
//  #define BAND    433E6 
//  #define PABOOST true 

  //LoR32u4II 868MHz or 915MHz (black board)
  #define SCK     15
  #define MISO    14
  #define MOSI    16
  #define SS      8
  #define RST     4
  #define DI0     7
  
  #define BAND    916750000
  #define POWER 20
  #define PABOOST 1 
  
int led = LOW;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, led);
  
  Serial.begin(9600);
  while (!Serial);

  LoRa.setPins(SS,RST,DI0);
  
  if (!LoRa.begin(BAND)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  
  LoRa.setTxPower(POWER, PABOOST);
  LoRa.setSignalBandwidth(62500);
  LoRa.setSpreadingFactor(9);
  LoRa.setCodingRate4(5);
  LoRa.disableCrc();

  // register the receive callback
  LoRa.onReceive(onReceive);

  // put the radio into receive mode
  LoRa.receive();
  Serial.println("Waiting...");
}

void loop() {
  // do nothing
}

static const int MSGSIZE = 80;
static const int REDUNDANCY = 20;
RS::ReedSolomon<MSGSIZE, REDUNDANCY> rs;
char decoded[MSGSIZE];
char encoded[MSGSIZE + REDUNDANCY];
char punctured[MSGSIZE + REDUNDANCY];

void onReceive(int plen) {
  Serial.println("Receiving...");
  led = ! led;
  digitalWrite(LED_BUILTIN, led);
  // received a packet

  memset(encoded, 0, sizeof(encoded));
  memset(decoded, 0, sizeof(decoded));
  memset(punctured, 0, sizeof(punctured));
  
  for (int i = 0; i < plen && i < sizeof(punctured); i++) {
    punctured[i] = LoRa.read();
  }

  memcpy(encoded, punctured, plen - REDUNDANCY);
  memcpy(encoded + MSGSIZE, punctured + plen - REDUNDANCY, REDUNDANCY);

  // print RSSI of packet
  Serial.print("pkt len ");
  Serial.print(plen);
  Serial.print(" RSSI ");
  Serial.println(LoRa.packetRssi());
  if (rs.Decode(encoded, decoded)) {
    Serial.println("\tPacket corrupted");
  } else {
    Serial.print("\tGood packet"); 
    String msg = decoded;
    Serial.print(" len ");
    Serial.print(plen - REDUNDANCY);
    Serial.print(" msg ");
    Serial.println(msg);
  }

}

