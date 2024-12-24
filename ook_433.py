#!/usr/bin/env python3

# Estimate signal strengh

import struct, numpy, sys, math, filters, ook, random
import paho.mqtt as pahomqtt
import paho.mqtt.client as mqtt

MQTT_PORT = 1883
MY_MQTT_PREFIX = 'Testooksdr%d' % random.randint(0, 1000000)
MQTT_CLIENT_ID = "%s" % MY_MQTT_PREFIX
MQTT_SERVER = None
MQTT_TOPIC = "stat/Test433/Keyfob"
mqtt_impl = None

gain = float(sys.argv[1])
if len(sys.argv) > 2:
    MQTT_SERVER = sys.argv[2]

if MQTT_SERVER:
    # Called on thread context
    def on_connect(_, __, flags, conn_result):
        print("MQTT connected", flags, conn_result)

    # Called on thread context
    def on_disconnect(_, userdata, rc):
        print("MQTT disconnected")

    if pahomqtt.__version__[0] > '1':
        mqtt_impl = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, MQTT_CLIENT_ID)
    else:
        mqtt_impl = mqtt.Client(MQTT_CLIENT_ID)

    mqtt_impl.on_connect = on_connect
    mqtt_impl.on_disconnect = on_disconnect
    mqtt_impl.connect_async(MQTT_SERVER, MQTT_PORT)
    mqtt_impl.loop_start() # starts thread

INPUT_RATE = 960000
FPS = 5
BANDWIDTH = 200000

# Length in µs per sample
SAMPLE_US = 1000000 / INPUT_RATE
# Minimum transition length to be considered part of a signal
TRANS_MIN_US = 150
# Maximum
TRANS_MAX_US = 1500
# Minimum transition length to be considered a signal preamble
PREAMBLE_MIN_US = 5000
# Maximum
PREAMBLE_MAX_US = 20000
# Transitions less than this are considered glitches
# We cannot filter everything below PREAMBLE_MIN_US because white noise would look like data.
# We need to let some noise to pass (GLITCH_US < x PREAMBLE_MIN_US) to be able to differentiate
# noise (likely when AGC is on) from signal
GLITCH_US = min(TRANS_MIN_US, PREAMBLE_MIN_US) / 4

remaining_data = b''

if_filter = filters.low_pass(INPUT_RATE, BANDWIDTH / 2, 48)
envelope_filter = filters.low_pass(INPUT_RATE, 1000000 / GLITCH_US, 48)

bgnoise = 0.66 / 128 # 2/3 of one bit x length of moving average
ook_threshold_db_up = 6 # dB above background noise
ook_threshold_db_down = 5
ook_threshold_mul_up = 10 ** (ook_threshold_db_up / 10)
ook_threshold_mul_down = 10 ** (ook_threshold_db_down / 10)

state = 0
length = 0
samples = []

def sgn(x):
    return (x >= 0) and +1 or -1

while True:
    # Ingest up to 1/FPS worth of data
    data = sys.stdin.buffer.read(INPUT_RATE * 2 // FPS)
    if not data:
        break
    data = remaining_data + data
    remaining_data = b''

    if len(data) < 4:
        remaining_data = data
        continue

    # Parse RTL-SDR I/Q format
    iqdata = numpy.frombuffer(data, dtype=numpy.uint8)
    iqdata = iqdata - 127.4
    iqdata = iqdata / 128.0
    iqdata = iqdata.view(complex)

    # Filter to bandwidth of interest
    iqdata = if_filter.feed(iqdata)
    # We are only interested in absolute amplitude
    iqdata = numpy.absolute(iqdata)
    # Detect envelope using a low-pass filter
    iqdata = envelope_filter.feed(iqdata)

    # Calculate background noise & moving average
    totenergy = numpy.sum(iqdata)
    counter = len(iqdata)
    avg = totenergy / counter
    weight = 0.01 / FPS
    bgnoise = bgnoise * (1.0 - weight) + avg * weight
    ook_threshold_up = bgnoise * ook_threshold_mul_up
    ook_threshold_down = bgnoise * ook_threshold_mul_down
    print("bgnoise (bits) avg=%f now=%f" % (bgnoise * 128, avg * 128))

    # Detect transitions
    for sample in iqdata:
        if state == 0:
            if sample > ook_threshold_up:
                # transition 0 -> 1
                samples.append(-int(length * SAMPLE_US))
                length = 0
                state = 1
        elif state == 1:
            if sample < ook_threshold_down:
                # transition 1 -> 0
                samples.append(+int(length * SAMPLE_US))
                length = 0
                state = 2
        elif state == 2:
            if sample > ook_threshold_up:
                # transition 0 -> 1 (alternate path)
                samples.append(-int(length * SAMPLE_US))
                length = 0
                state = 1
            elif length * SAMPLE_US > PREAMBLE_MAX_US:
                # early annotation of long 0 that serves as stop mark
                samples.append(-int(length * SAMPLE_US))
                length = 0
                state = 0
        length += 1

    # Cut signals and send to processing
    while True:
        # Detect preambles
        preambles = [i for i, val in enumerate(samples) if val < -PREAMBLE_MIN_US]
        if not preambles:
            samples = []
            break

        if len(preambles) >= 2:
            # Signal = samples between two preambles
            start = preambles[0] + 1
            stop = preambles[1]
            signal = samples[start:stop]
            samples = samples[stop:]

            bad1 = [i for i, val in enumerate(signal) if abs(val) < TRANS_MIN_US]
            bad2 = [i for i, val in enumerate(signal) if abs(val) > TRANS_MAX_US]
            if bad1 or bad2:
                # noise within signal
                continue

            result = ook.parse(signal)

            if result and mqtt_impl:
                mqtt_impl.publish(MQTT_TOPIC, result)
                print("Published MQTT topic")

        elif len(preambles) == 1:
            stop = preambles[0]
            samples = samples[stop:]
            break
