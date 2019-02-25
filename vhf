#!/bin/sh -x

# rtl_sdr -f 92.9M -s 960k -n 1920000 ta.iq
rtl_sdr -f 152500000 -g 30 -s 960k - | ./vhf.py
