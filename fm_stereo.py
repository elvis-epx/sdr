#!/usr/bin/env python3
# FM standalone stereo decoder
# Receives demodulated raw audio from e.g. fm1.py and decodes stereo

import struct, math, sys, numpy, filters

INPUT_RATE = 256000
OUTPUT_RATE = 32000

DECIMATION = INPUT_RATE / OUTPUT_RATE
assert DECIMATION == math.floor(DECIMATION)

FM_BANDWIDTH = 15000 # Hz
PILOT_TONE = 19000 # Hz
STEREO_CARRIER = 2 * PILOT_TONE # 38000 Hz

tau = 2 * math.pi

############ Pilot PLL state #################

# Phase of our local oscillator, that should follow cos() of the pilot.
# The 38kHz carrier is simply twice this phase.
pll = 0.0
# Phase advance per sample. It is tuned by the PLL, in case the pilot
# frequency is not exactly 19kHz (e.g. inaccuracy of SDR clock)
pll_step = tau * PILOT_TONE / INPUT_RATE
# PLL gains: how much a phase error corrects phase and frequency.
# Small values = slow but stable lock.
PLL_KP = 0.02
PLL_KI = 0.00002
last_pilot = 0.0

# Downsample mono audio
decimate1 = filters.decimator(DECIMATION)

# Deemph + Low-pass filter for mono (L+R) audio
lo = filters.deemphasis(INPUT_RATE, 75, FM_BANDWIDTH, 120)

# Downsample jstereo audio
decimate2 = filters.decimator(DECIMATION)

# Deemph + Low-pass filter for joint-stereo demodulated audio (L-R)
lo_r = filters.deemphasis(INPUT_RATE, 75, FM_BANDWIDTH, 120)

# Band-pass filter for stereo (L-R) modulated audio
hi = filters.band_pass(INPUT_RATE,
    STEREO_CARRIER - FM_BANDWIDTH, STEREO_CARRIER + FM_BANDWIDTH, 120)

# Filter to extract pilot signal
pilot = filters.band_pass(INPUT_RATE,
    STEREO_CARRIER / 2 - 100, STEREO_CARRIER / 2 + 100, 120)

# Each FIR filter delays the signal by half its length. The pilot filter
# is longer than the L-R band-pass filter, so the pilot we lock onto lags
# the L-R signal. Compensate that by advancing the carrier phase.
# (Without this, the carrier is ~280º off, and L-R comes out very weak.)
pilot_delay = len(pilot.coefs) // 2
jstereo_delay = len(hi.coefs) // 2
carrier_advance = 2 * (pilot_delay - jstereo_delay) * pll_step

# Per the standard, pilot is sin(t) and the stereo carrier is sin(2t):
# both cross zero at the same time. Our PLL follows cos() of the pilot,
# so pll = t - 90º, and sin(2t) = sin(2.pll + 180º) = cos(2.pll + 90º)
carrier_advance += math.pi / 2

# L-R goes through the band-pass filter, L+R does not. Delay L+R by the
# same amount, so both are aligned when we add/subtract them.
mono_delay = numpy.zeros(jstereo_delay)

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

    # At this point, samples contains two audio signals:
    # L+R (mono-compatible) and L-R (joint-stereo) modulated in AM-SC,
    # carrier 38kHz
    
    # Delay, downsample and low-pass L+R (mono) signal
    delayed = numpy.concatenate((mono_delay, samples))
    mono_delay = delayed[len(samples):]
    output_mono = lo.feed(delayed[:len(samples)])
    output_mono = decimate1.feed(output_mono)

    # Filter pilot tone
    detected_pilot = pilot.feed(samples)

    # Separate ultrasonic L-R signal by high-pass filtering
    output_jstereo_mod = hi.feed(samples)

    # Demodulate L-R, which is AM-SC with 38kHz carrier

    output_jstereo = numpy.empty(len(output_jstereo_mod))

    for n in range(0, len(output_jstereo_mod)):
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

        ############ L-R demodulation #################

        # Carrier is twice the pilot phase. Multiply by 2 because
        # cos(x) * cos(x) = 1/2 + cos(2x)/2, so we get (L-R)/2 otherwise.
        output_jstereo[n] = 2 * math.cos(2 * pll + carrier_advance) \
            * output_jstereo_mod[n]

        # Advance oscillator
        pll = (pll + pll_step) % tau

    # Downsample, Low-pass/deemphasis demodulated L-R
    output_jstereo = lo_r.feed(output_jstereo)
    output_jstereo = decimate2.feed(output_jstereo)

    assert len(output_jstereo) == len(output_mono)

    # Scale to 16-bit and divide by 2 for channel sum
    output_mono = numpy.multiply(output_mono, 32767 / 2.0)
    output_jstereo = numpy.multiply(output_jstereo, 32767 / 2.0)

    # Output stereo by adding or subtracting joint-stereo to mono
    output_left = output_mono + output_jstereo
    output_right = output_mono - output_jstereo

    # Interleave L and R samples using NumPy trickery
    output = numpy.empty(len(output_mono) * 2, dtype=output_mono.dtype)
    output[0::2] = output_left
    output[1::2] = output_right
    output = output.astype(int)

    sys.stdout.buffer.write(struct.pack('<%dh' % len(output), *output))
