# SDR and Modulation scripts

This repository is a loose collection of SDR, analog and digital modulation
scripts.

## Main folder

Contains SDR stuff. Highlights:

fm1.py: FM mono receiver. Check the scripts 'python\_fm\_mono' and 'python\_fm\_rt'
for usage.

fm1s.py: FM stereo receiver. Client scripts are 'python\_fm\_stereo' and
'python\_fm\_rt\_stereo'.

fastfm.pyx: FM stereo decoder with PLL written in Cython. Used by fm1s.py in
fast mode. Compile the module with 'make' and run fm1s.py with -o if your
machine can't decode stereo FM in realtime.

filters.py: Pure Python implementations of common filters: low-band, high-band,
passband, FM stereo deemphasis, and decimator.

power.py/power: Show signal strength of band using RTL-SDR. Note that unit is
dbFS, which is relative and not relatable to absolute units like dBmV/m or dBm.

nfm.py: Records multiple narrow FM channels, like VHF or Talkabout,
with squelch. Client scripts: talkabout and vhf.

dsd-gqrx: Gets UDP audio packets from GQRX or other SDR software, and feeds
into DSD to decode digital radio (DMR et al). DSD must be installed in your
system, version 1.7 or better is recommended (had no luck decoding DMR with 1.6).

dsd-rtl-save: usess rtl\_fm instead of GQRX as front-end. Saves audio as
$FREQ.wav.

The 'test\_samples' folder contains raw
I/Q data from RTL-SDR to test scripts without the need of a dongle (and a
live radio station).

am.py: Records multiple AM or SSB channels, like aviation and CB.

## APRS

The 'aprs' folder contains APRS scripts, mostly ones that use RTL-SDR as
radio and Direwolf as decoder.

## Mesh simulation

The 'mesh' folder contains mesh network
simulation, that I am working on as part of a LoRa-based ham project.

## Modulation

The 'modul' folder contains old and naïve implementations of a number of
modulation and demodulation techniques, both analog and digital.
