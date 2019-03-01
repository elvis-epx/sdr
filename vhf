#!/bin/sh -x

# Record narrow FM channels (most commonly VHF and UHF) as audio WAV files

FREQS="152772500"
rtl_sdr -f 153000000 -g 25 -s 900000 - | ./nfm.py 153000000 900000 $FREQS . $*
