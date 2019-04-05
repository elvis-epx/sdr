// LoRaMaDoR (LoRa-based mesh network for hams) project
// Copyright (c) 2019 PU5EPX

#include "Network.h"
#include "Log.h"
#include "FakeArduino.h"

static const unsigned int PKT_ID_RESET_TIME = 1200 * 1000; /* 20 minutes */

static const unsigned int CHK_BUSY_TIME = 1000;             /* 1 second */
static const unsigned int TX_BUSY_RETRY_TIME = 2000;             /* 2 seconds */

static const unsigned int ADJ_STATIONS_PERSIST = 3600 * 1000; /* 60 minutes */
static const unsigned int ADJ_STATIONS_CLEAN = 600 * 1000; /* 10 minutes */

static const unsigned int RECV_LOG_PERSIST = 600 * 1000; /* 10 minutes */
static const unsigned int RECV_LOG_CLEAN = 60 * 1000; /* 1 minute */

static const unsigned int AVG_BEACON_TIME = 600 * 1000; /* 10 minutes */
static const unsigned int AVG_FIRST_BEACON_TIME = 30 * 1000; /* 30 seconds */
static const char* BEACON_MSG = "73";

#define DEBUG 1

// Task IDs

static const int TASK_ID_TX = 1;
static const int TASK_ID_FWD = 2;
static const int TASK_ID_BEACON = 3;
static const int TASK_ID_ADJ_STATIONS = 4;
static const int TASK_ID_PKT_ID = 5;
static const int TASK_ID_RECV_LOG = 6;
static const int TASK_ID_CHK_BUSY = 7;

// Task who calls back Network::tx_task() 

class PacketTx: public Task {
public:
	PacketTx(const Buffer& encoded_packet,
		unsigned long int offset,
		TaskCallable* callback_target):
			Task(TASK_ID_TX, offset, callback_target),
			encoded_packet(encoded_packet) {}
	virtual ~PacketTx() {}
	const Buffer encoded_packet; // read by callback tx(), who downcasts Task to PacketTx
};

// Task who calls back Network::forward() 

class PacketFwd: public Task {
public:
	PacketFwd(const Ptr<Packet> packet,
		int rssi,
		bool we_are_origin,
		unsigned long int offset,
		TaskCallable* callback_target):
			Task(TASK_ID_FWD, offset, callback_target),
			packet(packet), rssi(rssi),
			we_are_origin(we_are_origin) {}
	virtual ~PacketFwd() {}
	virtual bool run(unsigned long int now) {
		Task::run(now);
		// forces this task to be one-off
		return false;
	}
	// read by callback forward(), who downcasts Task to PacketFwd
	const Ptr<Packet> packet;
	const int rssi;
	const bool we_are_origin;
};

/////////////////////// Network object singleton

static Ptr<Network> network_singleton = 0;

void config_net(const char *callsign) 
{
	if (! network_singleton) {
		network_singleton = new Network(callsign);
	}
}

Ptr<Network> net()
{
	return network_singleton;
}

// bridges C-style callback from LoRa/Radio module to network object
void radio_recv_trampoline(const char *recv_area, unsigned int plen, int rssi);

//////////////////////////// Network class proper

Network::Network(const char *callsign)
{
	my_callsign = Buffer(callsign);
	last_pkt_id = 0;
	task_mgr = new TaskManager();

	Task *beacon = new Task(TASK_ID_BEACON, fudge(AVG_FIRST_BEACON_TIME, 0.5), this);
	Task *clean_recv = new Task(TASK_ID_RECV_LOG, RECV_LOG_PERSIST, this);
	Task *clean_adj = new Task(TASK_ID_ADJ_STATIONS, ADJ_STATIONS_PERSIST, this);
	Task *id_reset = new Task(TASK_ID_PKT_ID, PKT_ID_RESET_TIME, this);
	Task *chk_busy = new Task(TASK_ID_CHK_BUSY, CHK_BUSY_TIME, this);

	task_mgr->schedule(beacon);
	task_mgr->schedule(clean_recv);
	task_mgr->schedule(clean_adj);
	task_mgr->schedule(id_reset);
	task_mgr->schedule(chk_busy);

	modifiers.push_back(new Rreqi());
	modifiers.push_back(new RetransBeacon());
	handlers.push_back(new Ping());
	handlers.push_back(new Rreq());

	setup_lora();
	lora_rx(radio_recv_trampoline);
	radio_busy = false;
}

Network::~Network()
{}

unsigned int Network::get_pkt_id()
{
	return ++last_pkt_id;
}

void Network::send(const char *to, const Params& params, const Buffer& msg)
{
	if (strlen(to) < 2 || strlen(to) > 7) {
		return;
	}
	Ptr<Packet> pkt = new Packet(to, my_callsign.cold(), get_pkt_id(), params, msg);
	sendmsg(pkt);
}

void Network::sendmsg(const Ptr<Packet> pkt)
{
	Task *fwd_task = new PacketFwd(pkt, 999, true, TASK_ID_FWD, this);
	task_mgr->schedule(fwd_task);
}

void Network::recv(Ptr<Packet> pkt)
{
#ifdef DEBUG
	logs("Received pkt", pkt->encode_l3().cold());
#endif
	for (unsigned int i = 0; i < handlers.size(); ++i) {
		Ptr<Packet> response = handlers[i]->handle(*pkt, my_callsign.cold());
		if (response) {
			sendmsg(response);
			return;
		}
	}
	// FIXME send to application level
}

void radio_recv_trampoline(const char *recv_area, unsigned int plen, int rssi)
{
	// ugly, but...
	network_singleton->radio_recv(recv_area, plen, rssi);
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
	Task *fwd_task = new PacketFwd(pkt, rssi, false, TASK_ID_FWD, this);
	task_mgr->schedule(fwd_task);
}

unsigned long int Network::beacon(unsigned long int, Task*)
{
	send("QB", Params(), Buffer(BEACON_MSG));
	return fudge(AVG_BEACON_TIME, 0.5);
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
#ifdef DEBUG
		logs("Forgotten packet", remove_list[i].cold());
#endif
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
#ifdef DEBUG
		logs("Forgotten station", remove_list[i].cold());
#endif
	}

	return ADJ_STATIONS_CLEAN;
}

unsigned long int Network::reset_pkt_id(unsigned long int, Task*)
{
	last_pkt_id = 0;
	return PKT_ID_RESET_TIME;
}

unsigned long int Network::tx(unsigned long int now, Task* task)
{
	if (radio_busy) {
		return TX_BUSY_RETRY_TIME;
	}
	const PacketTx* packet_task = dynamic_cast<PacketTx*>(task);
	lora_tx_async(packet_task->encoded_packet);
	radio_busy = true;
	return 0;
}

unsigned long int Network::check_radio_busy(unsigned long int, Task*)
{
	if (radio_busy) {
		if (! lora_tx_busy()) {
			radio_busy = false;
		}
	}
	return CHK_BUSY_TIME;
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
			return 0;
		}

		// Annotate to detect duplicates
		recv_log.put(pkt->signature(), RecvLogItem(rssi, now));
		// Transmit
		Task *tx_task = new PacketTx(pkt->encode_l2(), 50, this);
		task_mgr->schedule(tx_task);
		return 0;
	}

	// Packet originated from us but received via radio = loop
	if (my_callsign.str_equal(pkt->from())) {
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

	if (my_callsign.str_equal(pkt->to())) {
		// We are the final destination
		recv(pkt);
		return 0;
	}

	if (strcmp(pkt->to(), "QB") == 0 || strcmp(pkt->to(), "QC") == 0) {
		// We are just one of the destinations
		if (! pkt->params().has("R")) {
#ifdef DEBUG
			if (! adjacent_stations.has(pkt->from())) {
				logs("discovered neighbour", pkt->from());
			}
#endif
			adjacent_stations[pkt->from()] = AdjacentStation(rssi, now);
		}
		recv(pkt);
	}

	// Forward packet modifiers
	// They can add params and/or change msg
	for (unsigned int i = 0; i < modifiers.size(); ++i) {
		Ptr<Packet> modified_pkt = modifiers[i]->modify(*pkt, my_callsign.cold());
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

#ifdef DEBUG
	logi("relaying w/ delay", delay);
#endif

	Task *tx_task = new PacketTx(encoded_pkt, delay, this);
	task_mgr->schedule(tx_task);

	return 0;
}

unsigned long int Network::fudge(unsigned long int avg, double fudge)
{
	return arduino_random(avg * (1.0 - fudge), avg * (1.0 + fudge));
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
		case TASK_ID_PKT_ID:
			return reset_pkt_id(now, task);
		case TASK_ID_RECV_LOG:
			return clean_recv_log(now, task);
		case TASK_ID_CHK_BUSY:
			return check_radio_busy(now, task);
		default:
#ifdef DEBUG
			logi("invalid task id ", id);
#endif
	}
	return 0;
}
