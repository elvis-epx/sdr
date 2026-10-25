#!/usr/bin/env python3
# FM RDS decoder, without the 19kHz pilot
#
# Input: demodulated FM baseband ("MPX"), 16-bit LE mono at 256kHz, as
# produced by fm1.py. Output: decoded RDS information, as text.
#
# This is a variant of fm_rds.py that ignores the pilot tone and recovers
# everything from the RDS signal itself, so it also works with stations
# that transmit RDS in mono (no pilot). The price is two tracking loops
# instead of one PLL:
#
#   - a Costas loop recovers the 57kHz carrier (frequency and phase).
#     A plain PLL cannot be used, because the RDS carrier is suppressed:
#     there is no steady tone at 57kHz to lock onto.
#   - a bit clock loop (early-late gate) recovers the RDS bit timing,
#     whose rate is nominally 1187.5 bit/s but drifts with the SDR clock.
#
# Decoding steps:
#
#   1) RDS signal is mixed with a local 57kHz oscillator (NCO), using I/Q
#   2) The baseband signal is summed over each "chip" period, given by
#      the chip clock (16 chips per RDS bit, nominally 19000 chips/s)
#   3) Costas loop: the phase error of each chip corrects the NCO, so
#      the RDS signal ends up in the real part of the chips
#   4) Matched filter over 16 chips decodes biphase (Manchester) bits;
#      the early-late error corrects the chip clock, so bits are always
#      decided at their peak
#   5) Decode differential encoding
#   6) Find the 26-bit blocks using the CRC, assemble 4-block groups
#   7) Interpret the groups: station ID, name, text, clock...

import struct, math, sys, numpy, filters, cmath

debug_mode = "-d" in sys.argv

INPUT_RATE = 256000

RDS_CARRIER = 57000 # Hz
RDS_BANDWIDTH = 2400 # Hz, each side
RDS_BITRATE = RDS_CARRIER / 48 # 1187.5 bit/s
CHIPS_PER_BIT = 16
CHIP_RATE = RDS_BITRATE * CHIPS_PER_BIT # 19000 chips/s

tau = 2 * math.pi

# Filter to extract RDS signal
rds_signal = filters.band_pass(INPUT_RATE,
    RDS_CARRIER - RDS_BANDWIDTH, RDS_CARRIER + RDS_BANDWIDTH, 48)

############ Carrier (Costas loop) state #################

# Phase of our local 57kHz oscillator, that should follow the RDS carrier
nco = 0.0
# Phase advance per sample. Tuned by the Costas loop, since the carrier
# frequency is not exactly 57kHz (e.g. inaccuracy of SDR clock)
nco_step = tau * RDS_CARRIER / INPUT_RATE
# Costas loop gains, applied once per chip. Loop bandwidth is wide
# while acquiring and narrow (less noisy) once locked.
COSTAS_ACQ_KP = 0.03
COSTAS_ACQ_KI = 0.0003
COSTAS_KP = 0.01
COSTAS_KI = 0.00003
costas_kp = COSTAS_ACQ_KP
costas_ki = COSTAS_ACQ_KI
# Average of |chip|², used to normalize the phase error
chip_power = 0.0
# Average of the phase error, used to tell whether the loop is locked
costas_lock = 0.0

############ Chip and bit clock state #################

# Sum of mixed (baseband) RDS signal during the current chip
chip_sum = 0j
# Chip clock: 0..1 within the current chip
chip_clock = 0.0
# Chip clock advance per sample. Tuned by the bit clock loop.
chip_step = CHIP_RATE / INPUT_RATE
# Bit clock loop gains, applied once per bit
CLOCK_KP = 0.03
CLOCK_KI = 0.00005
# Early and late chips are this far (in chips) from the on-time one.
# 1 chip is too close: the matched filter peak is broad, so the
# difference between early and late would drown in noise.
EARLY_LATE = 4

# Last 16 chips (one bit worth)
chip_history = [ 0.0 for n in range(CHIPS_PER_BIT) ]
chip_count = 0
# Matched filter output of the last chips: early ... on time ... late
bit_values = [ 0.0 for n in range(2 * EARLY_LATE + 1) ]
last_raw_bit = 0
# Clock correction to apply in samples, spread along the next chips
pending_clock_shift = 0.0

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


def costas(chip):
    ''' Correct the 57kHz oscillator using the phase error of the chip '''
    global nco, nco_step, chip_power, costas_lock, costas_kp, costas_ki

    # BPSK: the chip should be on the real axis, either positive or
    # negative. Real x imag is positive when the chip is rotated
    # counterclockwise, negative when clockwise, regardless of the bit.
    # (It is |chip|².sin(2.error)/2, normalized to sin(2.error)/2.)
    chip_power = 0.999 * chip_power + 0.001 * abs(chip) ** 2
    if chip_power <= 0:
        return
    error = chip.real * chip.imag / chip_power

    # Correct phase and frequency (the latter is per sample, while
    # this runs once per chip, hence the division)
    nco += costas_kp * error
    nco_step += costas_ki * error / (INPUT_RATE / CHIP_RATE)

    # When locked, most of the energy is in the real part.
    # cos(2.error) is +1 if locked, averages to 0 if not.
    costas_lock = 0.999 * costas_lock + 0.001 * \
        (chip.real ** 2 - chip.imag ** 2) / chip_power
    if costas_lock > 0.5:
        costas_kp, costas_ki = COSTAS_KP, COSTAS_KI
    elif costas_lock < 0.3:
        costas_kp, costas_ki = COSTAS_ACQ_KP, COSTAS_ACQ_KI


def handle_chip(chip):
    ''' Process one chip (=1/16 of RDS bit) '''
    global chip_count, last_raw_bit, chip_step, pending_clock_shift

    costas(chip)

    # Costas loop keeps the RDS signal in the real part.
    # (Can be off by 180º, but differential coding takes care of that.)
    chip = chip.real

    chip_history.pop(0)
    chip_history.append(chip)
    chip_count += 1

    # Biphase coding: each bit is sent as two halves with opposite signals
    # (+- or -+). Compare first and second half of the last 16 chips.
    # (This is a matched filter.)
    half = CHIPS_PER_BIT // 2
    bit_values.pop(0)
    bit_values.append(sum(chip_history[:half]) - sum(chip_history[half:]))

    # The bit clock loop makes the "on time" chip, bit_values[EARLY_LATE],
    # fall on the bit peak, once every 16 chips. (So bits are decided
    # EARLY_LATE chips late, once the "late" chip is also known.) Unlike fm_rds.py, the bit boundary drifts in relation to a
    # fixed chip count, so the chip clock itself must be corrected.
    if chip_count % CHIPS_PER_BIT != 0:
        return

    early = bit_values[0]
    bit_value = bit_values[EARLY_LATE]
    late = bit_values[-1]

    # Early-late gate: if the late chip is stronger than the early one,
    # the peak is still ahead and we are deciding too early.
    # Error is normalized to -1..+1.
    strength = abs(early) + abs(late)
    if strength > 0:
        error = (abs(late) - abs(early)) / strength
        # Delay (or advance) the chip clock, and correct its rate.
        # The delay is in samples, spread along the next chips so the
        # chip sums are not distorted by a sudden jump.
        pending_clock_shift += CLOCK_KP * error * (INPUT_RATE / CHIP_RATE)
        chip_step -= CLOCK_KI * error * chip_step / CHIPS_PER_BIT

    # Differential coding: bit is 1 if it is different from the last one
    raw_bit = bit_value > 0 and 1 or 0
    handle_bit(raw_bit ^ last_raw_bit)
    last_raw_bit = raw_bit

    if debug_mode and chip_count % (CHIPS_PER_BIT * 1000) == 0:
        print("carrier=%.2fHz lock=%.2f bitrate=%.3fbps blocks=%d/%d" %
            (nco_step * INPUT_RATE / tau, costas_lock,
            chip_step * INPUT_RATE / CHIPS_PER_BIT,
            good_block_count, total_block_count),
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

    detected_rds = rds_signal.feed(samples)

    for n in range(0, len(samples)):
        sample_count += 1

        ############ RDS demodulation #################

        # Mix RDS with 57kHz to bring it to baseband.
        # e^(-jx) = cos(x) - j.sin(x)
        chip_sum += detected_rds[n] * cmath.exp(-1j * nco)

        nco += nco_step
        if nco >= tau:
            nco -= tau
        elif nco < 0:
            nco += tau

        # Advance chip clock, applying a bit of pending correction
        # (at most 1/8 of a sample per sample)
        shift = max(-0.125, min(0.125, pending_clock_shift))
        pending_clock_shift -= shift
        chip_clock += chip_step * (1.0 - shift)
        if chip_clock >= 1.0:
            chip_clock -= 1.0
            handle_chip(chip_sum)
            chip_sum = 0j

print("RDS blocks: %d good of %d" % (good_block_count, total_block_count),
    file=sys.stderr)
