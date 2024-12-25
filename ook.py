class OOKParser:
    # Generic ASK/OOK parser for 433MHz keyfobs
    # Assumption: every bit is composed of two level transitions

    name = ""
    bit_len_tolerance = 0.15

    # bitseq LH = bit is formed by a transition to low, then a transition to high
    #             and first transition is a delimiter
    #             Chirp examples: 001=1, 011=0
    # bitseq HL = bit is formed by a transition to high, then a transition to low
    #             and last transition is a delimiter
    #             Chirp examples: 1110=1, 1000=0
    bitseq = "LH"

    # bit1 LS = bit 1 is formed by a long-timed level followed by a short-timed level
    #           (and bit 0 is the opposite)
    #           Chirp examples: 1110=1 and 1000=0, or 001=1 and 011=0
    # bit1 SL = bit 1 is formed by a short-timed level followed by a long-timed level
    #           Chirp examples: 1110=0 and 1000=1, or 001=0 and 011=1
    bit1 = "LS" 

    def __init__(self, sequence):
        self.sequence = sequence
        self.code = 0
        self.note = ""

    def res(self):
        return "%s:%d%s" % (self.name, self.code, self.note)

    # Calculate average timing of each bit
    def bit_timing(self, bitcount, lh):
        tot = totsq = 0
        for i in range(0, bitcount):
            bittime = abs(self.sequence[i*2+lh]) + abs(self.sequence[i*2+1+lh])
            tot += bittime
            totsq += bittime * bittime
        mean = tot / bitcount
        return mean, (totsq / bitcount - mean * mean) ** 0.5

    # Find if timing of a single bit is off
    def anomalous_bit_timing(self, bitcount, lh, std, dev):
        for i in range(0, bitcount):
            bit_time = abs(self.sequence[i*2+lh]) + abs(self.sequence[i*2+1+lh])
            if bit_time < (std - dev) or bit_time > (std + dev):
                return (i, bit_time)
        return None

    # Parsing routine
    def parse(self):
        if len(self.sequence) != self.exp_sequence_len:
            return False

        bitcount = len(self.sequence) // 2
        lh = (self.bitseq == "LH") and 1 or 0
        ls = (self.bitseq == "LS") and 1 or 0

        bit_time, bit_time_dev = self.bit_timing(bitcount, lh)
        print(self.name, "> bit timing %dus stddev %dus" % (bit_time, bit_time_dev))

        anom = self.anomalous_bit_timing(bitcount, lh, bit_time, bit_time * self.bit_len_tolerance)
        if anom:
            print(self.name, "> bit timing anomaly %d timing %d" % anom)
            return False

        # Parse sane sequence
        self.code = 0
        for i in range(0, bitcount):
            lsbit = (abs(self.sequence[i*2+lh]) > abs(self.sequence[i*2+1+lh])) and 1 or 0
            self.code = (self.code << 1) | (lsbit ^ ls)

        return True

class HT6P20(OOKParser):
    name = "HT6P20"
    exp_sequence_len = 57
    bitseq = "LH" # low then high (011, 001)
    bit1 = "LS" # long then short (001)

    def parse(self):
        if not super().parse():
            return False
        if (self.code & 0xf) != 0b0101:
            print(self.name, "> suffix 0101 not found")
            return False
        return True

class EV1527(OOKParser):
    name = "EV1527"
    exp_sequence_len = 49
    bitseq = "HL" # high then low (1000 and 1110)
    bit1 = "LS" # long then short (1110)

parsers = [EV1527, HT6P20]
min_length = min([ parser.exp_sequence_len for parser in parsers ])

def parse(data):
    if len(data) < min_length:
        return None

    print("--- received data, length %d" % len(data))
    for parser_class in parsers:
        parser = parser_class(data)
        if parser.parse():
            res = parser.res()
            print(res)
            return res
    print("... failed to parse")
    return None
