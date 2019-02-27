#!/bin/sh -x

# rtl_sdr -f 152500000 -g 30 -s 1000k - | tee vhf.iq | ./vhf.py
rtl_sdr -f 153000000 -g 25 -s 1000k - | ./vhf.py
