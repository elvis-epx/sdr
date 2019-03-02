#!/bin/sh -x

# Record narrow FM channels (most commonly VHF and UHF) as audio WAV files

 FREQS="152770000 152700000"
CENTER="152500000"
BW=1000000
rtl_sdr -f $CENTER -g 25 -s $BW - | ./nfm.py $CENTER $BW $FREQS . $*
