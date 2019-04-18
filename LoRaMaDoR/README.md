# LoRaMaDoR - ham radio based on LoRa 

This project is inspired by LoRaHam. The major enhancement is a packet format
which is more powerful and more extensible, allowing for true network formation.
The implementation is a work in
progress, and more documentation will be added as time permits.

Users can use the protocol almost directly, with a "hands on" sensation,
the implementation fills in some information to compose a valid packet.
For example, a user types:

```
QC Chat tonight 22:00 at repeater 147.000
```

"QC" is the pseudo-destination for broadcast messages. The
actual transmitted packet (minus the FEC suffix) is something like:

```
QC<PP5UUU:33 Chat tonight 22:00 at repeater 147.000
```

And the forwared packet will be like like

```
QC<PP5UUU:33,R Chat tonight 22:00 at repeater 147.000
```

Example of beacon packet, sent automatically every 10 minutes by
every station:

```
QB<PU5EPX-11:2 bat=7.93V temp=25.4C wind=25.4kmh
```

How to ping another station:

```
PP5CRE-11:PING teste123
```

Actual traffic:
```
PP5CRE-11<PU5EPX-11:21,PING teste123
PU5EPX-11<PP5CRE-11:54,PONG teste123
```

Route request:

```
PP5CRE-11:RREQ teste123
```

Actual traffic:
```
PU5EPX-11<PP5CRE-11:RRSP teste123
PP5ABC rssi=-50
PU5XYZ rssi=-86
PP5CRE-11 rssi=-70  # routes added upstream
PU5ABC rssi=-34
PU5EPX-11 rssi=-62  # routes added downstream
```

## Packet format

A LoRaMaDoR packet is composed by three parts: header, payload and FEC code.
The header contains source callsign, destination callsign, and some 
parameters:

```
Destination<Source:Parameters Payload FEC
```

There shall not be spaces within the header. If there is a payload, it is separated
from the header by a single space. The FEC code is mandatory, and it is specified
in its own section later on.

Stations shall have 4 to 7 octets, shall not start with "Q", and may be suffixed
by an SSID. Special or pseudo-callsigns are: QB (beacon) for automatic broadcast
sent every 10 minutes, QC (think "CQ") for human broadcasting, and QL ("loopback")
for debugging/testing.

Parameters are a set of comma-separated list of items, for example:

```
123,A,B=C,D,E=FGH
```

The parameters can be in three formats: naked number, naked key, and key=value.

There shall be one and only one naked number in the parameter list: it is the
packet ID. Together with the source callsign, it uniquely identifies the packet
within the network in a 20-minute time window.

Keys (naked or not) must be composed of letters and numbers only, and must start
with a letter. Values may be composed of any characters except those used as delimiters
in the header (space, comma, equal, etc.)

Predefined parameters:

`R` signals the packet was forwarded. Stamped in packets with destination `QB` and `QC`.

`RREQ` (route request) asks for an automated `RRSP` response. Intermediate routers are
annotated in the message payload.

`PING` asks for an automated `PONG` response.

`T=number` is an optional timestamp, as the UNIX timestamp (seconds since 1/1/1970
0:00 UTC) subtracted by 1552265462. If sub-second precision is required, the number
can have decimal places.

`S=chars` is an optional digital signature of the payload.

## FEC code

Every packet is augmented by a 20-octet FEC (Forward Error Code) suffix.
The FEC is a Reed-Solomon code.

Since Reed-Solomon codes demand a fixed-size message, it is calculated as if
the network packet was padded with nulls (binary zeros) to size.

In order to contemplate low-memory microcontrollers, which cannot handle RS codes
above a certain size, two base sizes (and therefore two different RS codes) are
used: 100/80 and 200/180.

The reference FEC RS implementation is {https://github.com/simonyipeter/Arduino-FEC}.
