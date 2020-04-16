// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#include "Network.h"
#include "ArduinoBridge.h"

static const unsigned int TX_BUSY_RETRY_TIME = 1000;        /* 1 second */

static const unsigned int ADJ_STATIONS_PERSIST = 3600 * 1000; /* 60 minutes */
static const unsigned int ADJ_STATIONS_CLEAN = 600 * 1000; /* 10 minutes */

static const unsigned int RECV_LOG_PERSIST = 600 * 1000; /* 10 minutes */
static const unsigned int RECV_LOG_CLEAN = 60 * 1000; /* 1 minute */

static const unsigned int AVG_BEACON_TIME = 600 * 1000; /* 10 minutes */
static const unsigned int AVG_FIRST_BEACON_TIME = 10 * 1000; /* 30 seconds */
static const char* BEACON_MSG = "73";

static unsigned long int fudge(unsigned long int avg, double fudge)
{
	return arduino_random(avg * (1.0 - fudge), avg * (1.0 + fudge));
}


// Task IDs

static const int TASK_ID_TX = 1;
static const int TASK_ID_FWD = 2;
static const int TASK_ID_BEACON = 3;
static const int TASK_ID_ADJ_STATIONS = 4;
static const int TASK_ID_RECV_LOG = 6;

// Task who calls back Network::tx_task() 

class PacketTx: public Task {
public:
	PacketTx(const Buffer& encoded_packet,
		unsigned long int offset,
		TaskCallable* callback_target):
			Task(TASK_ID_TX, "tx", offset, callback_target),
			encoded_packet(encoded_packet) {}
	virtual ~PacketTx() {}
	const Buffer encoded_packet; // read by callback tx(), who downcasts Task to PacketTx
};

// Task who calls back Network::forward() 

class PacketFwd: public Task {
public:
	PacketFwd(const Ptr<Packet> packet,
		bool we_are_origin,
		unsigned long int offset,
		TaskCallable* callback_target):
			Task(TASK_ID_FWD, "fwd", offset, callback_target),
			packet(packet),
			we_are_origin(we_are_origin) {}
	virtual ~PacketFwd() {}
	virtual bool run(unsigned long int now) {
		Task::run(now);
		// forces this task to be one-off
		return false;
	}
	// read by callback forward(), who downcasts Task to PacketFwd
	const Ptr<Packet> packet;
	const bool we_are_origin;
};

// bridges C-style callback from LoRa/Radio module to network object
void radio_recv_trampoline(const char *recv_area, unsigned int plen, int rssi);

//////////////////////////// Network class proper

Ptr<Network> trampoline_target = 0;

Network::Network(const Callsign &callsign)
{
	if (! callsign.is_valid()) {
		return;
	}

	my_callsign = callsign;
	last_pkt_id = arduino_nvram_id_load();

	Task *beacon = new Task(TASK_ID_BEACON, "beacon", fudge(AVG_FIRST_BEACON_TIME, 0.5), this);
	Task *clean_recv = new Task(TASK_ID_RECV_LOG, "recv_log", RECV_LOG_PERSIST, this);
	Task *clean_adj = new Task(TASK_ID_ADJ_STATIONS, "adj_list", ADJ_STATIONS_PERSIST, this);

	task_mgr.schedule(beacon);
	task_mgr.schedule(clean_recv);
	task_mgr.schedule(clean_adj);

	modifiers.push_back(new Rreqi());
	modifiers.push_back(new RetransBeacon());
	handlers.push_back(new Ping());
	handlers.push_back(new Rreq());

	setup_lora();
	trampoline_target = this;
	lora_rx(radio_recv_trampoline);
}

Network::~Network()
{}

unsigned int Network::get_next_pkt_id()
{
	if (++last_pkt_id > 9999) {
		last_pkt_id = 1;
	}
	arduino_nvram_id_save(last_pkt_id);
	return last_pkt_id;
}

unsigned int Network::get_last_pkt_id() const
{
	return last_pkt_id;
}

void Network::send(const Callsign &to, const Params& params, const Buffer& msg)
{
	Ptr<Packet> pkt = new Packet(to, me(), get_next_pkt_id(), params, msg);
	sendmsg(pkt);
}

void Network::sendmsg(const Ptr<Packet> pkt)
{
	Task *fwd_task = new PacketFwd(pkt, true, TASK_ID_FWD, this);
	task_mgr.schedule(fwd_task);
}

void Network::recv(Ptr<Packet> pkt)
{
	// logs("Received pkt", pkt->encode_l3().cold());
	for (unsigned int i = 0; i < handlers.size(); ++i) {
		Ptr<Packet> response = handlers[i]->handle(*pkt, me());
		if (response) {
			sendmsg(response);
			return;
		}
	}
	app_recv(pkt);
}

void radio_recv_trampoline(const char *recv_area, unsigned int plen, int rssi)
{
	// ugly, but...
	trampoline_target->radio_recv(recv_area, plen, rssi);
}

void Network::radio_recv(const char *recv_area, unsigned int plen, int rssi)
{
	Ptr<Packet> pkt = Packet::decode_l2(recv_area, plen, rssi);
	if (!pkt) {
		logi("Invalid packet received, error =", Packet::get_decode_error());
		return;
	}
	// logi("Good packet, RSSI =", rssi);
	Task *fwd_task = new PacketFwd(pkt, false, TASK_ID_FWD, this);
	task_mgr.schedule(fwd_task);
}

unsigned long int Network::beacon(unsigned long int, Task*)
{
	send(Callsign("QB"), Params(), Buffer(BEACON_MSG));
#ifdef UNDER_TEST
	unsigned long int next = fudge(10000, 0.5);
#else
	unsigned long int next = fudge(AVG_BEACON_TIME, 0.5);
#endif
	logi("Next beacon in ", next);
	return next;
}

unsigned long int Network::clean_recv_log(unsigned long int now, Task*)
{
	Vector<Buffer> remove_list;
	long int cutoff = now - RECV_LOG_PERSIST;

	const Vector<Buffer>& keys = recv_log.keys();
	for (unsigned int i = 0; i < keys.size(); ++i) {
		const RecvLogItem& v = recv_log[keys[i]];
		if ((long int) v.timestamp < cutoff) {
			remove_list.push_back(keys[i]);
		}
	}

	for (unsigned int i = 0; i < remove_list.size(); ++i) {
		recv_log.remove(remove_list[i]);
		// logs("Forgotten packet", remove_list[i].cold());
	}

	return RECV_LOG_CLEAN;
}

unsigned long int Network::clean_adjacent_stations(unsigned long int now, Task*)
{
	Vector<Buffer> remove_list;
	long int cutoff = now - ADJ_STATIONS_PERSIST;

	const Vector<Buffer>& keys = adjacent_stations.keys();
	for (unsigned int i = 0; i < keys.size(); ++i) {
		const AdjacentStation& v = adjacent_stations[keys[i]];
		if ((long int) v.timestamp < cutoff) {
			remove_list.push_back(keys[i]);
		}
	}

	for (unsigned int i = 0; i < remove_list.size(); ++i) {
		adjacent_stations.remove(remove_list[i]);
		logs("Forgotten station", remove_list[i].cold());
	}

	return ADJ_STATIONS_CLEAN;
}

unsigned long int Network::tx(unsigned long int now, Task* task)
{
	/*
	if (lora_tx_busy()) {
		return TX_BUSY_RETRY_TIME;
	}
	*/
	const PacketTx* packet_task = static_cast<PacketTx*>(task);
	lora_tx(packet_task->encoded_packet);
	return 0;
}

unsigned long int Network::forward(unsigned long int now, Task* task)
{
	const PacketFwd* fwd_task = static_cast<PacketFwd*>(task);
	Ptr<Packet> pkt = fwd_task->packet;
	int rssi = pkt->rssi();
	bool we_are_origin = fwd_task->we_are_origin;

	if (we_are_origin) {
		// Loopback handling
		if (me().equal(pkt->to()) || pkt->to().is_localhost()) {
			recv(pkt);
			return 0;
		}

		// Annotate to detect duplicates
		recv_log.put(pkt->signature(), RecvLogItem(rssi, now));
		// Transmit
		Task *tx_task = new PacketTx(pkt->encode_l2(), 50, this);
		task_mgr.schedule(tx_task);
		logs("tx ", pkt->encode_l3().cold());
		return 0;
	}

	// Packet originated from us but received via radio = loop
	if (me().equal(pkt->from())) {
		// logs("pkt loop", pkt->signature());
		return 0;
	}

	// Discard received duplicates
	if (recv_log.has(pkt->signature())) {
		// logs("pkt dup", pkt->signature());
		return 0;
	}
	recv_log.put(pkt->signature(), RecvLogItem(rssi, now)); 

	if (me().equal(pkt->to())) {
		// We are the final destination
		recv(pkt);
		return 0;
	}

	if (pkt->to().equal("QB") || pkt->to().equal("QC")) {
		// We are just one of the destinations
		if (! pkt->params().has("R")) {
			if (! adjacent_stations.has(pkt->from().buf())) {
				logs("discovered neighbour", pkt->from().buf().cold());
			}
			adjacent_stations[pkt->from().buf()] = AdjacentStation(rssi, now);
		}
		recv(pkt);
	}

	// Forward packet modifiers
	// They can add params and/or change msg
	for (unsigned int i = 0; i < modifiers.size(); ++i) {
		Ptr<Packet> modified_pkt = modifiers[i]->modify(*pkt, me());
		if (modified_pkt) {
			// replace packet by modified vesion
			pkt = modified_pkt;
			break;
		}
	}

	// Diffusion routing
	Buffer encoded_pkt = pkt->encode_l2();

	// TX delay in bits: packet size x stations nearby
	unsigned long int bit_delay = encoded_pkt.length() * 8;
	bit_delay *= 2 * (1 + adjacent_stations.count());

	// convert delay in bits to milisseconds
	// e.g. 900 bits @ 600 bps = 1500 ms
	unsigned long int delay = bit_delay * 1000 / lora_speed_bps();

	logi("relaying w/ delay", delay);

	Task *tx_task = new PacketTx(encoded_pkt, delay, this);
	logs("relay ", pkt->encode_l3().cold());
	task_mgr.schedule(tx_task);

	return 0;
}

unsigned long int Network::task_callback(int id, unsigned long int now, Task* task)
{
	switch (id) {
		case TASK_ID_BEACON:
			return beacon(now, task);
		case TASK_ID_TX:
			return tx(now, task);
		case TASK_ID_FWD:
			return forward(now, task);
		case TASK_ID_ADJ_STATIONS:
			return clean_adjacent_stations(now, task);
		case TASK_ID_RECV_LOG:
			return clean_recv_log(now, task);
		default:
			logi("invalid task id ", id);
	}
	return 0;
}

void Network::run_tasks(unsigned long int millis)
{
	task_mgr.run(millis);
}

Callsign Network::me() const {
	return my_callsign;
}
