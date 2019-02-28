#!/bin/sh -x

FREQS="152772500"
rtl_sdr -f 153000000 -g 25 -s 900000 - | ./vhf.py 153000000 900000 $FREQS . $*
