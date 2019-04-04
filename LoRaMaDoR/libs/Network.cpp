// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#include "Network.h"

static const unsigned int PKT_ID_RESET_TIME = 1200 * 1000; /* 20 minutes */

static const unsigned int ADJ_STATIONS_PERSIST = 3600 * 1000; /* 60 minutes */
static const unsigned int ADJ_STATIONS_CLEAN = 600 * 1000; /* 10 minutes */

static const unsigned int RECV_PKT_PERSIST = 600 * 1000; /* 10 minutes */
static const unsigned int RECV_PKT_CLEAN = 60 * 1000; /* 1 minute */

static const unsigned int AVG_BEACON_TIME = 600 * 1000; /* 10 minutes */
static const unsigned int AVG_FIRST_BEACON_TIME = 30 * 1000; /* 30 seconds */
static const char* BEACON_MSG = "73";

#define DEBUG 1

unsigned long int PacketFwd::run(unsigned long int now)
{
	Task::run(unsigned long int now);
	// forces this task to be one-off
	return 0;
}

unsigned long int PacketTx::run(unsigned long int now)
{
	Task::run(unsigned long int now);
	// forces this task to be one-off
	return 0;
}

Network::Network(const char *callsign)
{
	my_callsign = Buffer(callsign);
	last_pkt_id = 0;
	task_mgr = new TaskManager();

	Task *beacon = new Task(Network::random(AVG_FIRST_BEACON_TIME, 0.5), this, &Network::beacon);
	Task *clean_recv = new Task(RECV_PKT_PERSIST, this, &Network::clean_recv_log);
	Task *clean_adj = new Task(ADJ_STATIONS_PERSIST, this, &Network::adjacent_stations_clean);
	Task *id_reset = new Task(PKT_ID_RESET_TIME, this, &Network::reset_pkt_id);

	task_mgr->schedule(beacon);
	task_mgr->schedule(clean_recv);
	task_mgr->schedule(clean_adj);
	task_mgr->schedule(id_reset);

	modifiers.push_back(new Rreqi());
	modifiers.push_back(new RetransBeacon());
	handlers.push_back(new Ping());
	handlers.push_back(new Rreq());
}

Network::~Network()
{}

unsigned int Network::get_pkt_id()
{
	return ++task_pkt_id;
}

void Network::send(const char *to, const Dict &params, const Buffer& msg)
{
	if (strlen(to) < 2 || strlen(to) > 7) {
		return;
	}
	Ptr<Packet> pkt = new Packet(to, self.callsign, self.get_pkt_id(), params, msg);
	sendmsg(pkt);
}

void Network::sendmsg(const Ptr<Packet> pkt)
{
	Task *fwd_task = new PacketFwd(pkt, 999, true, this, &Network::forward);
	task_mgr->schedule(fwd_task);
}

void Network::recv(Ptr<Packet> pkt)
{
#ifdef DEBUG
	logs("Received pkt", pkt.encode_l3().cold());
#endif
	for (unsigned int i = 0; i < handlers.size(); ++i) {
		Ptr<Packet> response = handlers[i](*pkt);
		if (response) {
			sendmsg(response);
			return;
		}
	}
	// FIXME send to higher level
}

void Network::radio_recv(const char *recv_area, unsigned int plen, int rssi)
{
	Ptr<Packet> pkt = Packet::decode_l2(recv_area, plen);
	if (!pkt) {
#ifdef DEBUG
		logi("Invalid packet received, error =", Packet::get_decode_error());
#endif
		return;
	}
#ifdef DEBUG
	logi("Good packet, RSSI =", rssi);
#endif
	Task *fwd_task = new PacketFwd(pkt, rssi, false, this, &Network::forward);
	task_mgr->schedule(fwd_task);
}

unsigned long int Network::beacon(Task*)
{
	send("QB", Params(), Buffer(BEACON_MSG));
	return Network::random(AVG_BEACON_TIME, 0.5);
}

unsigned long int Network::clean_recv_log(unsigned long int now, Task*)
{
	Vector<Buffer> remove_list;
	long int cutoff = now - RECV_PKT_PERSIST;

	const Vector<Buffer>& keys = known_pkts.keys();
	for (unsigned int i = 0; i < keys.size(); ++i) {
		const RecvLogItem& v = known_pkts[keys[i]];
		if (v.timestamp < cutoff) {
			remove_list.push_back(keys[i]);
		}
	}

	for (unsigned int i = 0; i < remove_list.size(); ++i) {
		recv_log.remove(remove_list[i]);
#ifdef DEBUG
		logs("Forgotten packet", remove_list[i]);
#endif
	}

	return RECV_PKT_CLEAN;
}

unsigned long int Network::clean_adjacent_stations(Task*)
{
	Vector<Buffer> remove_list;
	long int cutoff = now - ADJ_STATIONS_PERSIST;

	const Vector<Buffer>& keys = adjacent_stations.keys();
	for (unsigned int i = 0; i < keys.size(); ++i) {
		const AdjacentStation& v = adjacent_stations[keys[i]];
		if (v.timestamp < cutoff) {
			remove_list.push_back(keys[i]);
		}
	}

	for (unsigned int i = 0; i < remove_list.size(); ++i) {
		adjacent_stations.remove(remove_list[i]);
#ifdef DEBUG
		logs("Forgotten station", remove_list[i].cold())
#endif
	}

	return ADJ_STATIONS_CLEAN;
}

unsigned long int Network::reset_pkt_id(Task*)
{
	last_pkt_id = 0;
	return PKT_ID_RESET_TIME;
}

unsigned long int Network::tx(Task* task)
{
	const PacketTx* packet_task = dynamic_cast<PacketTx*>(task);
	lora_tx(packet_task->encoded_packet);
	return 0;
}

unsigned long int Network::forward(unsigned long int now, Task* task)
{
	const PacketFwd* fwd_task = dynamic_cast<PacketFwd*>(task);
	Ptr<Packet> pkt = fwd_task->packet;
	int rssi = fwd_task->rssi;
	bool we_are_origin = fwd_task->we_are_origin;

	if (we_are_origin) {
		// Loopback handling
		if (my_callsign.str_equal(pkt->to()) ||
				strcmp("QL", pkt->to()) == 0) {
			recv(pkt);
			return;
		}

		// Annotate to detect duplicates
		recv_log.put(pkt->signature(), RecvLogItem(rssi, now));
		// Transmit
		Task *tx_task = new PacketTx(pkt->l2_encode(), 1, this, &Network::tx);
		task_mgr->schedule(tx_task);
		return 0;
	}

	// Packet originated from us but received via radio = loop
	if (my_callsign.str_equal(pkt->from()) {
#ifdef DEBUG
		logs("pkt loop", pkt->signature());
#endif
		return 0;
	}

	// Discard received duplicates
	if (recv_log.has(pkt->signature())) {
#ifdef DEBUG
		logs("pkt dup", pkt->signature());
#endif
		return 0;
	}
	recv_log.put(pkt->signature(), RecvLogItem(rssi, now)); 

	if (my_callsign.str_equal(pkt->to()) {
		// We are the final destination
		recv(pkt);
		return;
	}

	if (strcmp(pkt->to(), "QB") == 0 || strcmp(pkt->to(), "QC") == 0) {
		// We are just one of the destinations
		if (! pkt->params().has("R")) {
#ifdef DEBUG
			if (! adjacent_stations.has(pkt->from())) {
				logs("discovered neighbour", pkt.from());
			}
#endif
			adjacent_stations[pkt->from()] = AdjacentStation(rssi, now);
		}
		self.recv(pkt);
	}

	// Forward packet modifiers
	// They can add params and/or change msg
	for (unsigned int i = 0; i < modifiers.size(); ++i) {
		Ptr<Packet> modified_pkt = modifiers[i](pkt, my_callsign.cold());
		if (modified_pkt) {
			// replace packet by modified vesion
			pkt = modified_pkt;
			break;
		}
	}

	// Diffusion routing
	Buffer encoded_pkt = pkt->encode();

	// TX delay in bits: packet size x stations nearby
	unsigned long int bit_delay = encoded_pkt.length() * 8;
	bit_delay *= 2 * (1 + adjacent_stations.count());

	// convert delay in bits to milisseconds
	// e.g. 900 bits @ 600 bps = 1500 ms
	unsigned long int delay = bit_delay * 1000 / speed_bps();

#ifdef DEBUG
	logi("relaying w/ delay", delay);
#endif

	Task *tx_task = new PacketTx(encoded_pkt, delay, this, &Network::tx);
	task_mgr->schedule(tx_task);

	return 0;
}

unsigned long int Network::random(unsigned long int avg, double fudge)
{
	return arduino_random(avg * (1.0 - fudge), avg * (1.0 + fudge));
}
