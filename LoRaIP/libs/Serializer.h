#ifndef __SERIALIZER_H
#define __SERIALIZER_H

// add octet to tx buffer, stuffed
bool serializer_tx_add(char);

// get unstuffed tx packet
bool serializer_tx_getbuf(char **pkt, unsigned int *len);

// get stuffed rx buffer from received packet
bool serializer_rx_get(

serializer_rx_stuff(const char *pkt, unsigned int pktlen, char **buf, unsigned int *len);

#endif
