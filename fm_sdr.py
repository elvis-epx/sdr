#!/usr/bin/env python3
# FM SDR demodulator

import struct, math, random, sys, numpy, filters, time

debug_mode = "-d" in sys.argv
disable_pll = "--disable-pll" in sys.argv

INPUT_RATE = 256000

PILOT_TONE = 19000 # Hz
RDS_CARRIER = 57000 # Hz

pll = 0.0
last_pilot = 0.0
deviation_avg = 0.0
last_deviation_avg = 0.0
tau = 2 * math.pi

# Filter to extract pilot signal
pilot = filters.band_pass(INPUT_RATE, PILOT_TONE - 100, PILOT_TONE + 100, 120)

# Filter RDS signal
rds_signal = filters.band_pass(INPUT_RATE, RDS_CARRIER - 2000, RDS_CARRIER + 2000, 48)

remaining_data = b''

while True:
    # Ingest 0.1s worth of data
    data = sys.stdin.buffer.read((INPUT_RATE * 2) // 10)
    if not data:
        break
    data = remaining_data + data

    if len(data) < 2:
        remaining_data = data
        continue

    # Save one sample to next batch, and the odd byte if exists
    if len(data) % 2 == 1:
        print("Odd byte, that's odd", file=sys.stderr)
        remaining_data = data[-3:]
        data = data[:-1]
    else:
        remaining_data = data[-2:]

    # Convert 16-bit LE samples to list of integer
    output_raw = struct.unpack('<%dh' % (len(data) // 2), data) 
    # Convert to NumPy arary
    output_raw = numpy.array(output_raw)
    # Convert to float -1.0..+1.0
    output_raw = numpy.multiply(output_raw, 1.0 / 32768.0)

    # Filter pilot tone
    detected_pilot = pilot.feed(output_raw)

    # Filter RDS signal 
    detected_rds = rds_signal.feed(output_raw)

    for n in range(0, len(detected_pilot)):
        # FIXME demodulate RDS
 
        # Advance carrier
        pll = (pll + tau * RDS_CARRIER / INPUT_RATE) % tau

        if disable_pll:
            continue

        ############ Carrier PLL #################

        # Detect pilot zero-crossing
        cur_pilot = detected_pilot[n]
        zero_crossed = (cur_pilot * last_pilot) <= 0
        crossed_up = cur_pilot > last_pilot
        last_pilot = cur_pilot
        if not zero_crossed:
            continue

        # When pilot is at 90º or 270º, carrier should be around 270º or 90º, respectively
        # Pilot crosses up at 270º
        ideal = (not crossed_up) and (-math.pi / 2) or (math.pi / 2)
        deviation = pll - ideal
        if deviation > math.pi:
            # 350º => -10º
            deviation -= tau

        deviation_avg = 0.999 * deviation_avg + 0.001 * deviation
        rotation = deviation_avg - last_deviation_avg
        last_deviation_avg = deviation_avg

        if abs(deviation_avg) > math.pi / 8:
            # big phase deviation, reset PLL
            print("Resetting PLL", )
            pll = ideal
            pll = (pll + tau * RDS_CARRIER / INPUT_RATE) % tau
            deviation_avg = 0.0
            last_deviation_avg = 0.0

        # Translate rotation to frequency deviation e.g.
        # cos(tau + 3.6º) = cos(1.01 * tau)
        # cos(tau - 9º) = cos(tau * 0.975)
                    #
        # Overcorrect by 1% to (try to) sync phase,
                    # otherwise only the frequency would be synced.

        RDS_CARRIER /= (1 + (rotation * 1.01) / tau)

        print("%d pll=%f deviation=%f deviationavg=%f rotation=%f freq=%f" %
            (n,
            pll * 180 / math.pi,
            deviation * 180 / math.pi,
            deviation_avg * 180 / math.pi,
            rotation * 180 / math.pi,
            RDS_CARRIER))

        if RDS_CARRIER > 58000 or RDS_CARRIER < 56000:
            print("PLL failure")
            sys.exit(1)
