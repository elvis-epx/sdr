#!/usr/bin/env python3
# FM RDS decoder
#
# Input: demodulated FM baseband ("MPX"), 16-bit LE mono at 256kHz, as
# produced by fm1.py. Output: decoded RDS information, as text.
#
# The MPX signal contains, among other things:
#
#   19kHz pilot tone
#   57kHz RDS subcarrier, BPSK modulated, carrier suppressed
#
# The RDS subcarrier is exactly 3x the pilot frequency, and the RDS bit
# rate (1187.5 bit/s) is exactly the pilot frequency divided by 16. So,
# everything we need to know about timing can be derived from the pilot.
#
# Decoding steps:
#
#   1) PLL locks into the 19kHz pilot
#   2) RDS signal is mixed with 3x the PLL phase (57kHz), so it goes
#      down to baseband. We use I/Q (cos and sin) because the phase of
#      RDS relative to the pilot is not known beforehand.
#   3) The baseband signal is summed over each pilot cycle, generating
#      one "chip" per pilot cycle, so 16 chips per RDS bit.
#   4) Find the phase of RDS signal, rotate chips so the signal is real
#   5) Find the bit boundaries, decode biphase (Manchester) bits
#   6) Decode differential encoding
#   7) Find the 26-bit blocks using the CRC, assemble 4-block groups
#   8) Interpret the groups: station ID, name, text, clock...

import struct, math, sys, numpy, filters, cmath

debug_mode = "-d" in sys.argv

INPUT_RATE = 256000

PILOT_TONE = 19000 # Hz
RDS_CARRIER = 3 * PILOT_TONE # 57000 Hz
RDS_BANDWIDTH = 2400 # Hz, each side
CHIPS_PER_BIT = 16 # 19000 / 1187.5

tau = 2 * math.pi

# Filter to extract pilot signal
pilot = filters.band_pass(INPUT_RATE, PILOT_TONE - 100, PILOT_TONE + 100, 120)

# Filter to extract RDS signal
rds_signal = filters.band_pass(INPUT_RATE,
    RDS_CARRIER - RDS_BANDWIDTH, RDS_CARRIER + RDS_BANDWIDTH, 48)

############ Pilot PLL state #################

# Phase of our local oscillator, that should follow cos() of the pilot
pll = 0.0
# Phase advance per sample. It is tuned by the PLL, in case the pilot
# frequency is not exactly 19kHz (e.g. inaccuracy of SDR clock)
pll_step = tau * PILOT_TONE / INPUT_RATE
# PLL gains: how much a phase error corrects phase and frequency.
# Small values = slow but stable lock.
PLL_KP = 0.02
PLL_KI = 0.00002
last_pilot = 0.0

############ Chip state #################

# Sum of mixed (baseband) RDS signal during the current pilot cycle
chip_sum = 0j

############ RDS phase and bit timing state #################

# Average of chip², used to find the RDS signal phase
chip_sq_avg = 0j
# Last 16 chips (one bit worth)
chip_history = [ 0.0 for n in range(CHIPS_PER_BIT) ]
chip_count = 0
# Average bit "strength" for each of the 16 possible bit boundaries
timing_strength = [ 0.0 for n in range(CHIPS_PER_BIT) ]
last_raw_bit = 0

############ Block sync state #################

# RDS block = 16 bits of data + 10 bits of checkword.
# The checkword is a CRC, XORed with an "offset word" that tells
# the block position in the group (A, B, C or D).
# Block C' replaces C in version B groups.
CRC_POLY = 0b10110111001 # x^10 + x^8 + x^7 + x^5 + x^4 + x^3 + 1
OFFSET_WORDS = { 0b0011111100: 'A', 0b0110011000: 'B', 0b0101101000: 'C',
                 0b1101010000: "C'", 0b0110110100: 'D' }
BLOCK_INDEX = { 'A': 0, 'B': 1, 'C': 2, "C'": 2, 'D': 3 }

block_register = 0
bits_in_block = 0
synced = False
expected_block = 0
bad_blocks = 0
group = [ None, None, None, None ]

good_block_count = 0
total_block_count = 0

############ Decoded data #################

PTY_NAMES = [ "None", "News", "Current affairs", "Information", "Sport",
    "Education", "Drama", "Culture", "Science", "Varied", "Pop music",
    "Rock music", "Easy listening", "Light classical", "Serious classical",
    "Other music", "Weather", "Finance", "Children's", "Social affairs",
    "Religion", "Phone-in", "Travel", "Leisure", "Jazz", "Country",
    "National music", "Oldies", "Folk music", "Documentary", "Alarm test",
    "Alarm" ]

pi_code = None
pty = None
station_name = [ None ] * 8
last_station_name = None
radio_text = [ ' ' ] * 64
radio_text_ab = None
last_radio_text = None
sample_count = 0


def report(msg):
    print("[%6.1fs] %s" % (sample_count / INPUT_RATE, msg))
    sys.stdout.flush()


def to_char(c):
    # RDS character set is ASCII-like in the printable range
    return 32 <= c < 127 and chr(c) or '?'


def crc_remainder(word):
    ''' Remainder of the 26-bit word divided by CRC polynomial '''
    # Plain long division in binary (XOR = subtraction)
    for bit in range(25, 9, -1):
        if word & (1 << bit):
            word ^= CRC_POLY << (bit - 10)
    return word


def handle_group(a, b, c, d):
    global pi_code, pty, last_station_name, radio_text_ab, last_radio_text

    # Block A always contains PI (station ID)
    # Block B has group type, version, and program type (PTY)
    if a is not None and a != pi_code:
        pi_code = a
        report("PI: %04X" % pi_code)

    if b is None:
        return

    group_type = b >> 12
    version_b = (b >> 11) & 1
    if (b >> 5) & 0x1f != pty:
        pty = (b >> 5) & 0x1f
        report("PTY: %d (%s)" % (pty, PTY_NAMES[pty]))

    if group_type == 0 and d is not None:
        # Group 0A/0B: basic info. Block D contains 2 chars of station name
        segment = b & 0x03
        station_name[segment * 2] = to_char(d >> 8)
        station_name[segment * 2 + 1] = to_char(d & 0xff)
        if None not in station_name:
            name = ''.join(station_name)
            if name != last_station_name:
                last_station_name = name
                report("PS: '%s'" % name)

    elif group_type == 2:
        # Group 2A: radio text, 4 chars per group (blocks C and D)
        # Group 2B: radio text, 2 chars per group (block D)
        ab = (b >> 4) & 1
        if ab != radio_text_ab:
            # Flag toggled: new text, clear old one
            radio_text_ab = ab
            radio_text[:] = [ ' ' ] * 64
        segment = b & 0x0f
        if not version_b and c is not None and d is not None:
            chars = [ c >> 8, c & 0xff, d >> 8, d & 0xff ]
            pos = segment * 4
        elif version_b and d is not None:
            chars = [ d >> 8, d & 0xff ]
            pos = segment * 2
        else:
            return
        for i, ch in enumerate(chars):
            radio_text[pos + i] = ch == 0x0d and ' ' or to_char(ch)
        text = ''.join(radio_text).rstrip()
        if 0x0d in chars or segment == 15:
            # End of text: print it
            if text and text != last_radio_text:
                last_radio_text = text
                report("RT: '%s'" % text)

    elif group_type == 4 and not version_b and c is not None and d is not None:
        # Group 4A: clock time and date (UTC)
        mjd = ((b & 0x03) << 15) | (c >> 1)
        hour = ((c & 1) << 4) | (d >> 12)
        minute = (d >> 6) & 0x3f
        offset = (d & 0x1f) * 30 # local time offset in minutes
        if (d >> 5) & 1:
            offset = -offset
        # Modified Julian Date to calendar date (formula from RDS standard)
        y = int((mjd - 15078.2) / 365.25)
        m = int((mjd - 14956.1 - int(y * 365.25)) / 30.6001)
        day = mjd - 14956 - int(y * 365.25) - int(m * 30.6001)
        k = (m == 14 or m == 15) and 1 or 0
        year = 1900 + y + k
        month = m - 1 - k * 12
        report("CT: %04d-%02d-%02d %02d:%02d UTC, local offset %+.1fh" %
            (year, month, day, hour, minute, offset / 60))


def handle_bit(bit):
    ''' Find RDS blocks in the bit stream '''
    global block_register, bits_in_block, synced, expected_block, bad_blocks
    global good_block_count, total_block_count

    block_register = ((block_register << 1) | bit) & 0x3ffffff
    bits_in_block += 1

    if not synced:
        # Try every bit position until we find a valid block
        block_type = OFFSET_WORDS.get(crc_remainder(block_register), None)
        if block_type is None:
            return
        synced = True
        expected_block = BLOCK_INDEX[block_type]
        if debug_mode:
            print("Block sync acquired", file=sys.stderr)
    elif bits_in_block < 26:
        return

    # A whole block has arrived (we are synced)
    bits_in_block = 0
    total_block_count += 1
    block_type = OFFSET_WORDS.get(crc_remainder(block_register), None)

    if block_type is not None and BLOCK_INDEX[block_type] == expected_block:
        good_block_count += 1
        bad_blocks = 0
        group[expected_block] = block_register >> 10
    else:
        # Corrupted block, discard
        group[expected_block] = None
        bad_blocks += 1
        if bad_blocks >= 10:
            # Too many errors in sequence, sync probably lost
            synced = False
            if debug_mode:
                print("Block sync lost", file=sys.stderr)

    if expected_block == 3:
        handle_group(*group)
        group[:] = [ None, None, None, None ]
    expected_block = (expected_block + 1) % 4


def handle_chip(chip):
    ''' Process one chip (=1/16 of RDS bit) '''
    global chip_sq_avg, chip_count, last_raw_bit

    # Find RDS phase. Squaring the chip removes the BPSK modulation
    # (+1 and -1 both become +1), only twice the phase remains.
    chip_sq_avg = 0.999 * chip_sq_avg + 0.001 * chip * chip
    rds_phase = cmath.phase(chip_sq_avg) / 2

    # Rotate chip so the RDS signal is all in the real part.
    # (Can be off by 180º, but differential coding takes care of that.)
    chip = (chip * cmath.exp(-1j * rds_phase)).real

    chip_history.pop(0)
    chip_history.append(chip)
    chip_count += 1

    # Biphase coding: each bit is sent as two halves with opposite signals
    # (+- or -+). Compare first and second half of the last 16 chips.
    # (This is a matched filter.)
    half = CHIPS_PER_BIT // 2
    bit_value = sum(chip_history[:half]) - sum(chip_history[half:])

    # At the right bit boundary, bit_value is strongest. Since bit
    # clock comes from pilot, the right boundary does not drift.
    offset = chip_count % CHIPS_PER_BIT
    timing_strength[offset] = 0.99 * timing_strength[offset] + 0.01 * abs(bit_value)
    best_offset = timing_strength.index(max(timing_strength))
    if offset != best_offset:
        return

    # Differential coding: bit is 1 if it is different from the last one
    raw_bit = bit_value > 0 and 1 or 0
    handle_bit(raw_bit ^ last_raw_bit)
    last_raw_bit = raw_bit

    if debug_mode and chip_count % (CHIPS_PER_BIT * 1000) == best_offset:
        print("pilot=%.2fHz rds_phase=%.1fº bit_offset=%d blocks=%d/%d" %
            (pll_step * INPUT_RATE / tau, rds_phase * 180 / math.pi,
            best_offset, good_block_count, total_block_count),
            file=sys.stderr)


remaining_data = b''

while True:
    # Ingest 0.1s worth of data
    data = sys.stdin.buffer.read((INPUT_RATE * 2) // 10)
    if not data:
        break
    data = remaining_data + data

    # Keep odd byte, if exists, to next batch
    if len(data) % 2 == 1:
        remaining_data = data[-1:]
        data = data[:-1]
    else:
        remaining_data = b''

    # Convert 16-bit LE samples to NumPy array of float -1.0..+1.0
    samples = numpy.frombuffer(data, dtype='<i2') / 32768.0

    detected_pilot = pilot.feed(samples)
    detected_rds = rds_signal.feed(samples)

    for n in range(0, len(samples)):
        sample_count += 1

        ############ Pilot PLL #################

        # Detect pilot zero-crossing
        cur_pilot = detected_pilot[n]
        if cur_pilot * last_pilot < 0:
            # Find where, between samples, the crossing happened
            # (linear interpolation), and our phase at that moment
            fraction = cur_pilot / (cur_pilot - last_pilot)
            pll_at_crossing = pll - fraction * pll_step

            # cos() crosses down at 90º and crosses up at 270º (-90º)
            ideal = cur_pilot < 0 and (math.pi / 2) or (-math.pi / 2)

            # Phase error, wrapped to -180º..+180º
            error = (pll_at_crossing - ideal + math.pi) % tau - math.pi

            # Correct phase and frequency
            pll -= PLL_KP * error
            pll_step -= PLL_KI * error
        last_pilot = cur_pilot

        ############ RDS demodulation #################

        # Mix RDS with 57kHz (3x pilot) to bring it to baseband.
        # e^(-jx) = cos(x) - j.sin(x)
        chip_sum += detected_rds[n] * cmath.exp(-3j * pll)

        # Advance oscillator. Each pilot cycle completes one chip.
        pll += pll_step
        if pll >= tau:
            pll -= tau
            handle_chip(chip_sum)
            chip_sum = 0j

print("RDS blocks: %d good of %d" % (good_block_count, total_block_count),
    file=sys.stderr)
