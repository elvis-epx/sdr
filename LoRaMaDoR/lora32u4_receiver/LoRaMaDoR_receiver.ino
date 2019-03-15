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
  #define PABOOST true 
  
int led = LOW;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, led);
  
  Serial.begin(9600);
  while (!Serial);

  Serial.println("LoRa Receiver Callback");
  LoRa.setPins(SS,RST,DI0);
  if (!LoRa.begin(BAND,PABOOST)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  LoRa.setSpreadingFactor(9);
  LoRa.setTxPower(0);
  LoRa.setSignalBandwidth(125000);
  LoRa.setCodingRate4(5);
  // LoRa.enableCrc();

  // register the receive callback
  LoRa.onReceive(onReceive);

  // put the radio into receive mode
  LoRa.receive();
  Serial.println("Waiting...");
}

void loop() {
  // do nothing
}

static const int MSGSIZ = 40;
static const int REDUNDANCY = 10;
RS::ReedSolomon<MSGSIZ, REDUNDANCY> rs1;
unsigned char message_frame[MSGSIZ + 1];
unsigned char encoded_message[MSGSIZ + REDUNDANCY + 1];

void onReceive(int packetSize) {
  Serial.println("Receiving...");
  led = ! led;
  digitalWrite(LED_BUILTIN, led);
  // received a packet

  memset(encoded_message, 0, sizeof(encoded_message));
  memset(message_frame, 0, sizeof(message_frame));
  
  for (int i = 0; i < packetSize && i < (MSGSIZ + REDUNDANCY); i++) {
    encoded_message[i] = LoRa.read();
  }

  // print RSSI of packet
  Serial.print("pkt len ");
  Serial.print(packetSize);
  Serial.print(" RSSI ");
  Serial.print(LoRa.packetRssi());
  Serial.print(" SNR ");
  Serial.println(LoRa.packetSnr());
    for (int i = 0; i < (MSGSIZ + REDUNDANCY); ++i) {
      Serial.print((int) encoded_message[i]);
      Serial.print(" ");
    }
    Serial.println();
  if (rs1.Decode(encoded_message, message_frame)) {
    Serial.println("\tPacket corrupted");
  } else {
    Serial.print("\tGood packet");
    int net_length = message_frame[0]; 
    if (net_length >= MSGSIZ) {
      Serial.println("\tPacket corrupted (size obviously wrong)");      
    }
    String msg = (char*) message_frame;
    Serial.print(" len ");
    Serial.print(net_length);
    Serial.print(" msg ");
    Serial.println(msg.substring(1, net_length + 1));
  }

}

