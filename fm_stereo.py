#!/usr/bin/env python3
# FM standalone stereo decoder
# Receives demodulated raw audio from e.g. fm1.py and decodes stereo

import struct, math, random, sys, numpy, filters, time

INPUT_RATE = 256000
OUTPUT_RATE = 32000

DECIMATION = INPUT_RATE / OUTPUT_RATE
assert DECIMATION == math.floor(DECIMATION)

FM_BANDWIDTH = 15000 # Hz
STEREO_CARRIER = 38000 # Hz

pll = math.pi - random.random() * 2 * math.pi
last_pilot = 0.0
deviation_avg = math.pi - random.random() * 2 * math.pi
last_deviation_avg = deviation_avg
tau = 2 * math.pi

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

last_angle = 0.0
remaining_data = b''

while True:
    # Ingest 0.1s worth of data
    data = sys.stdin.buffer.read((INPUT_RATE * 2) // 10)
    if not data:
        break
    data = remaining_data + data

    # Save one sample to next batch, and the odd byte if exists
    if len(data) % 2 == 1:
        print("Odd byte, that's odd", file=sys.stderr)
        remaining_data = data[-3:]
        data = data[:-1]
    else:
        remaining_data = data[-2:]

    # Convert 16-bit LE samples to NumPy array of float -1.0..+1.0
    samples = numpy.frombuffer(data, dtype='<i2') / 32768.0

    # At this point, samples contains two audio signals:
    # L+R (mono-compatible) and L-R (joint-stereo) modulated in AM-SC,
    # carrier 38kHz
    
    # Downsample and low-pass L+R (mono) signal
    output_mono = lo.feed(samples)
    output_mono = decimate1.feed(output_mono)

    # Filter pilot tone
    detected_pilot = pilot.feed(samples)

    # Separate ultrasonic L-R signal by high-pass filtering
    output_jstereo_mod = hi.feed(samples)

    # Demodulate L-R, which is AM-SC with 53kHz carrier

    output_jstereo = []

    for n in range(0, len(output_jstereo_mod)):
        # Advance carrier
        pll = (pll + tau * STEREO_CARRIER / INPUT_RATE) % tau

        # Standard demodulation
        output_jstereo.append(math.cos(pll) * output_jstereo_mod[n])

        ############ Carrier PLL #################

        # Detect pilot zero-crossing
        cur_pilot = detected_pilot[n]
        zero_crossed = (cur_pilot * last_pilot) <= 0
        last_pilot = cur_pilot
        if not zero_crossed:
            continue

        # When pilot is at 90º or 270º, carrier should be around 180º
        # t=0    => cos(t) = 1,  cos(2t) = 1
        # t=π/2  => cos(t) = 0,  cos(2t) = -1
        # t=π    => cos(t) = -1, cos(2t) = 1
        # t=-π/2 => cos(t) = 0,  cos(2t) = -1
        ideal = math.pi
        deviation = pll - ideal
        if deviation > math.pi:
            # 350º => -10º
            deviation -= tau
        deviation_avg = 0.99 * deviation_avg + 0.01 * deviation
        rotation = deviation_avg - last_deviation_avg
        last_deviation_avg = deviation_avg

        if abs(deviation_avg) > math.pi / 8:
            # big phase deviation, reset PLL
            # print("Resetting PLL", file=sys.stderr)
            pll = ideal
            pll = (pll + tau * STEREO_CARRIER / INPUT_RATE) % tau
            deviation_avg = 0.0
            last_deviation_avg = 0.0

        # Translate rotation to frequency deviation e.g.
        # cos(tau + 3.6º) = cos(1.01 * tau)
        # cos(tau - 9º) = cos(tau * 0.975)
                       #
        # Overcorrect by 5% to (try to) sync phase,
                       # otherwise only the frequency would be synced.

        STEREO_CARRIER /= (1 + (rotation * 1.05) / tau)

        '''
        print("%d deviationavg=%f rotation=%f freq=%f" %
            (n,
            deviation_avg * 180 / math.pi,
            rotation * 180 / math.pi,
            STEREO_CARRIER),
            file=sys.stderr)
        time.sleep(0.05)
        '''

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
