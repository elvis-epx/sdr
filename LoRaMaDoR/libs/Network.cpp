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

	Task *beacon = new Task(Network::random(AVG_FIRST_BEACON_TIME), this, &Network::beacon);
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
	// FIXME message log
	for (unsigned int i = 0; i < handlers.size(); ++i) {
		Ptr<Packet> response = handlers[i](*pkt);
		if (response) {
			sendmsg(response);
			return;
		}
	}
	// FIXME send to higher level
}

// called indirectly by Radio, takes a trampoline somewhere to adapt 
// function callback to this method callback (FIXME)
void Network::radio_recv(const char *recv_area, unsigned int plen, int rssi)
{
	Ptr<Packet> pkt = Packet::decode_l2(recv_area, plen);
	if (!pkt) {
		log(10, "Invalid packet received, error =", Packet::get_decode_error());
		return;
	}
	log(80, "Good packet, RSSI =", rssi);
	Task *fwd_task = new PacketFwd(pkt, rssi, false, this, &Network::forward);
	task_mgr->schedule(fwd_task);
}

unsigned long int Network::beacon(Task*)
{
	send("QB", Params(), Buffer("73"));
	return Network::random(AVG_BEACON_TIME);
}

unsigned long int Network::clean_recv_log(unsigned long int now, Task*)
{
	Vector<Buffer> remove_list;
	long int cutoff = now - RECV_PKT_PERSIST;

	for k, v in self.known_pkts.items():
		if v < cutoff:
			remove_list.append(k)

	for (unsigned int i = 0; i < remove_list.size(); ++i) {
		recv_log.remove(remove_list[i]);
		log(50, "Forgotten packet", 0)
	}

	return RECV_PKT_CLEAN;
}

unsigned long int Network::clean_adjacent_stations(Task*)
{
	remove_list = []
	cutoff = time.time() - 3600
	for k, v in self.adjacent_stations.items():
		if v["last_q"] < cutoff:
			remove_list.append(k)
	for k in remove_list:
		if VERBOSITY > 10:
			print("Removed adjacent station %s" % k)
		del self.adjacent_stations[k]

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

unsigned long int Network::forward(Task* task)
{
	const PacketFwd* fwd_task = dynamic_cast<PacketFwd*>(task);
	Ptr<Packet> pkt = fwd_task->packet;
	int radio_rssi = fwd_task->rssi;
	bool we_are_origin = fwd_task->we_are_origin;

	# Sanity check
	if not pkt.to or not pkt.fr0m:
		print("%s: bad pkt %s" % (self.callsign, pkt))
		return

	if we_are_origin:
		if pkt.to in ("QL", self.callsign):
			# Destination is loopback
			self.recv(pkt)
			return

		# Annotate to detect duplicates
		self.known_pkts[pkt.signature()] = time.time()

		# Transmit
		self.radio.send(self.callsign, pkt.encode())
		return

	# Packet originated from us but received via radio = loop
	if pkt.fr0m == self.callsign:
		if VERBOSITY > 80:
			print("%s *loop* %s" % (self.callsign, pkt))
		return

	# Discard received duplicates
	if pkt.signature() in self.known_pkts:
		if VERBOSITY > 80:
			print("%s *dup* %s" % (self.callsign, pkt))
		return
	self.known_pkts[pkt.signature()] = time.time()

	if pkt.to == self.callsign:
		# We are the final destination
		self.recv(pkt)
		return
	elif pkt.to in ("QB", "QC"):
		# We are just one of the destinations
		if "R" not in pkt.params:
			if pkt.fr0m not in self.adjacent_stations and VERBOSITY > 50:
				print("%s: discovered neighbour %s" % (self.callsign, pkt.fr0m))
			self.adjacent_stations[pkt.fr0m] = \
				{"last_q": time.time(), "rssi": radio_rssi}
		self.recv(pkt)

	# Forward packet modifiers
	# They can add params and/or change msg
	for mod in fwd_modifiers:
		if mod.match(pkt):
			more_params, msg = mod.handle(self, pkt)
			if msg is not None:
				pkt = pkt.change_msg(msg)
			if more_params:
				for k, v in more_params.items():
					pkt = pkt.append_param(k, v)

	# Diffusion routing
	delay = random.random() * len(pkt.encode()) * 8 * 2 * (1 + len(self.adjacent_stations)) / 1400
	if VERBOSITY > 50:
		print("%s: relaying with delay %d: %s" % (self.callsign, delay * 1000, pkt))

	Task *tx_task = new PacketTx(pkt->encode(), this, &Network::tx);
	task_mgr->schedule(tx_task);

	return 0;
}

unsigned long int Network::random(unsigned long int avg)
{
	// add 50% fudge to an average time
	return arduino_random(avg / 2, 3 * avg / 2);
}
