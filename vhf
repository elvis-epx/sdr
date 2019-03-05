#!/bin/bash -x

# Record narrow FM channels (most commonly VHF and UHF) as audio WAV files

# FREQS="145330000"

FREQS="153727500 153827500 153990000 154350000"
# CENTR="153700000"

# Determine center automatically
s=0
n=0
for f in $FREQS; do
	s=$(($s + $f))
	n=$(($n + 1))
done
STEP=2500
CENTR=$(($s / $n - 20000))
CENTR=$(($CENTR / $STEP))
CENTR=$(($CENTR * $STEP))

BW=1000000
rtl_sdr -f $CENTR -g 25 -s $BW - | ./nfm.py $CENTR $BW $STEP $FREQS . $*
