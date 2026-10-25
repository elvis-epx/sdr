# How fm_rds.py decodes RDS

This document explains, step by step and in plain terms, how `fm_rds.py`
turns the output of `fm1.py` into station names, RadioText and clock time.
The longest section is about the relationship between the 19 kHz pilot tone
and the RDS bits, because it is the trick that keeps the decoder simple.

## 1. What is in the signal

`fm1.py` demodulates FM and outputs the **baseband** (also called the
"multiplex" or MPX signal), sampled at 256,000 samples per second. Once FM is
demodulated, one radio station's baseband holds several signals side by side,
each in its own frequency range:

```
   0 - 15 kHz   mono audio (L+R)
       19 kHz   pilot tone: a pure, steady sine wave
  23 - 53 kHz   stereo difference (L-R), centred at 38 kHz = 2 x 19 kHz
       57 kHz   RDS, centred at 57 kHz = 3 x 19 kHz, about +/-2.4 kHz wide
```

The pilot tone is there so stereo receivers can rebuild the 38 kHz carrier.
For us, it does something more useful: **the station generates both the RDS
carrier and the RDS bit clock from the same master clock as the pilot.**

- RDS carrier: 57,000 Hz = exactly 3 x 19,000 Hz
- RDS bit rate: 1,187.5 bits/s = exactly 19,000 / 16 (the standard defines it
  as 57,000 / 48, which is the same thing)

So if we follow the pilot accurately, we automatically know the exact RDS
carrier frequency and the exact length of one RDS bit. Many RDS decoders have
to recover these two things separately from the noisy RDS signal itself.
`fm_rds.py` gets them for free from the pilot.

What the pilot does **not** tell us, and what we have to find out by other
means:

1. the **phase** of the 57 kHz RDS carrier relative to the pilot (section 5),
2. **which** of the pilot cycles a bit starts on (section 6).

## 2. Separating pilot and RDS

Two band-pass filters pick the two signals of interest out of the baseband:

- `pilot`: lets through 18.9-19.1 kHz, so only the pilot tone is left;
- `rds_signal`: lets through 54.6-59.4 kHz, so only RDS is left.

Everything else (audio, stereo) is thrown away.

## 3. Following the pilot: the PLL

A **PLL** (phase-locked loop) is a local oscillator that keeps adjusting
itself until it runs in lockstep with an incoming signal. Think of it as a
person clapping along to music, speeding up or slowing down a little whenever
they notice they are ahead of or behind the beat.

In the code, the oscillator is just a number, `pll`: an angle from 0 to 360
degrees (0 to 2π radians) that says "where we are" inside the current pilot
cycle. We want `cos(pll)` to match the pilot tone. Every sample, `pll`
advances by `pll_step`, which is initially 19,000 / 256,000 of a full turn.

How it corrects itself:

- Every time the filtered pilot crosses zero, we know exactly where the real
  pilot is in its cycle: a cosine crosses zero going *down* at 90 degrees and
  going *up* at 270 degrees.
- We compare that with where our own oscillator was at that moment (with
  interpolation between samples, for precision). The difference is the
  **phase error**.
- A small fraction of the error (`PLL_KP`) is subtracted from the phase,
  and an even smaller fraction (`PLL_KI`) is subtracted from the step, so
  the oscillator also learns the true frequency.

The frequency correction matters because the RTL-SDR dongle's clock is not
perfect: in the test recording the pilot first appears at about 19,011 Hz
and the PLL slowly pulls in to 19,000 Hz. Whatever the apparent frequency,
the PLL follows it, and since RDS is tied to the pilot, the RDS carrier and bit
rate "move" by exactly the same proportion. Nothing else needs to compensate.

Why a PLL and not the filtered pilot directly? The PLL averages its
corrections over many cycles, so its phase is much cleaner than any single
zero crossing, which noise can push around.

## 4. Bringing RDS down to zero frequency: "chips"

### 4.1 Mixing

The RDS signal sits around 57 kHz. To read it, we shift it down to 0 Hz
(**baseband**). This is done by multiplying it by a 57 kHz oscillator, which
we can build from the PLL: three times the pilot phase is a 57 kHz phase that
is locked to the pilot.

```python
chip_sum += detected_rds[n] * cmath.exp(-3j * pll)
```

`exp(-3j * pll)` is a complex number: `cos(3·pll) - j·sin(3·pll)`. Using both
cosine and sine (the "I" and "Q" parts) means that we capture the RDS signal
whatever its phase is. If we multiplied by cosine only, an RDS carrier
90 degrees off from our cosine would cancel itself out and vanish.

What comes out of this multiplication is:

- the RDS data at 0 Hz, multiplied by a **fixed** complex number
  `e^(jθ)`, where θ is the (still unknown) phase difference between the
  station's 57 kHz carrier and our 3 x pilot oscillator; plus
- an unwanted copy at 114 kHz (57 + 57).

### 4.2 Summing over one pilot cycle

Instead of a low-pass filter, the code simply **adds up** the mixed samples
during one full pilot cycle (from one time `pll` wraps past 360 degrees to the
next one, about 13.5 samples). Each sum is called a **chip**.

This does two things at once:

- It removes the unwanted 114 kHz copy. 114 kHz is 6 x 19 kHz, so during
  one pilot cycle it spins around exactly 6 times, and a full turn adds up
  to zero.
- It reduces the sample rate from 256,000 to 19,000 per second, which is
  still plenty: RDS changes much more slowly than one pilot cycle.

Because a bit is 16 pilot cycles long, **every RDS bit is exactly 16 chips**,
always, no matter how far off the dongle's clock is. That is the reason for
`CHIPS_PER_BIT = 16`.

## 5. The RDS phase relative to the pilot

This is the first of the two unknowns.

### 5.1 Why it is unknown

The standard requires the station to lock the 57 kHz carrier to the third
harmonic of the pilot. That fixes the *frequency* precisely. But the *phase*
we observe, the angle θ between "3 x our PLL phase" and the actual RDS
carrier, depends on things we do not control:

- how the station's equipment aligns them (in practice it varies from station
  to station);
- delays inside our own receiver. The pilot filter has 126 taps and the RDS
  filter only 22, so the pilot comes out of its filter about 52 samples
  (≈ 200 µs) later than RDS. During those 200 µs a 57 kHz carrier turns
  through about 11.6 cycles, so the delay alone shifts the apparent phase
  by roughly two hundred degrees.

What matters is that **θ does not change** (or changes very slowly), because
both the carrier and our oscillator are locked to the same pilot. If our
57 kHz were not locked to the pilot, θ would keep spinning, and we would need
a second PLL for the RDS carrier. Locking to the pilot reduces the problem to
"measure one constant angle".

### 5.2 How the angle is measured: squaring

RDS uses **BPSK** (binary phase-shift keying): the 57 kHz carrier is either
sent normally or upside down (inverted, i.e. shifted by 180 degrees). After
mixing, each chip is therefore roughly:

```
chip = a · e^(jθ)        where a is a positive or negative real number
```

Draw the chips on a plane (real part horizontal, imaginary part vertical).
They all fall on a single straight line through the origin, tilted at angle
θ, some on one side of the origin (`a > 0`) and some on the other (`a < 0`):

```
        imag
         |      * *
         |   * *          <- chips with a > 0
         | *
  -------+-------- real
       * |
    * *  |                <- chips with a < 0
  * *    |
```

We want the angle of that line. Averaging the chips directly does not work:
the positive and negative ones cancel out. The trick is to **square** them:

```
chip² = a² · e^(j2θ)
```

`a²` is always positive, so the sign of the data disappears and all squared
chips point in the same direction, 2θ. They can now be averaged
(`chip_sq_avg`, a slow running average over roughly the last 1,000 chips, or
about 50 ms), and the angle of that average, divided by two, is θ:

```python
chip_sq_avg = 0.999 * chip_sq_avg + 0.001 * chip * chip
rds_phase = cmath.phase(chip_sq_avg) / 2
```

Then each chip is rotated back by θ, so the data lies along the real axis
and the imaginary part (which now contains only noise) can be discarded:

```python
chip = (chip * cmath.exp(-1j * rds_phase)).real
```

In the test recording, this angle stays around -37 degrees, as the `-d`
output shows (`rds_phase=-37.2º`).

### 5.3 The 180-degree ambiguity

Halving an angle has two answers: θ and θ + 180 degrees both square to the
same 2θ. So we may rotate the line the "wrong way round", and every chip comes
out with its sign flipped. We cannot tell which one is right, and **we don't
need to**: RDS uses differential coding (section 7), which gives the same
data whether the signal is upside down or not. If the estimate ever jumps from
one answer to the other (possible when θ is close to ±90 degrees), only
the single bit at the jump is corrupted.

## 6. The RDS bit timing relative to the pilot

This is the second unknown.

### 6.1 What we know and what we don't

Every bit is exactly 16 chips. But our chips are counted from wherever the
program happened to start, so we don't know **which** of every 16 chips is the
first chip of a bit. There are only 16 possibilities, numbered 0 to 15
(`chip_count % 16`).

Since the bit clock is derived from the same master clock as the pilot, the
right possibility **never drifts**: once we find it, it remains valid for as
long as the PLL stays locked. (Without the pilot, we would need a clock
recovery loop that constantly adjusts the bit timing, as most RDS decoders do.)

Small print: a bit boundary is tied to a fixed point inside a pilot cycle,
but not necessarily the point where our chips begin (the positive peak of the
pilot). So the true boundary may fall inside a chip. That smears less than one
chip out of 16 into the neighbouring bit, which is a small loss and can be
ignored.

### 6.2 Biphase (Manchester) coding

RDS does not send a bit as a single "high" or "low" level. Each bit is sent as
two halves of opposite sign, either `+` then `-`, or `-` then `+`:

```
 raw bit 1:   + + + + + + + + - - - - - - - -
 raw bit 0:   - - - - - - - - + + + + + + + +
              <-- 8 chips --> <-- 8 chips -->
```

(The real waveform is smooth rather than square, but the idea is the same.)
The point of this is that every bit has a change in the middle, which
makes it easy to locate the bit boundaries.

### 6.3 Finding the right offset

The code keeps the last 16 chips in `chip_history`, and after every new chip
computes:

```python
bit_value = sum(first 8 chips) - sum(last 8 chips)
```

This is a **matched filter**: a ruler with the shape of a bit, `+` then `-`.
Where the 16 chips line up with a real bit, the two halves have opposite signs,
the subtraction adds them together, and `|bit_value|` is large, every time.

If the ruler is misaligned, for example by half a bit (8 chips), it straddles
the second half of one bit and the first half of the next. Whether these two
halves have opposite signs depends on the data, so `|bit_value|` is large only
some of the time and close to zero the rest. On average, it is clearly smaller.

So, for each of the 16 possible offsets, the code keeps a running average of
`|bit_value|` in `timing_strength`, and the offset with the largest average is
the right one:

```
offset:     0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
strength:   .  .  .  .  .  .  :  :  |  |  #  |  |  :  .  .
                                          ^
                                    best_offset = 10
```

Only when `chip_count % 16` equals `best_offset` is a bit actually decided:
its sign (`bit_value > 0`) is the **raw bit**. In the test recording the best
offset settles on 10 and stays there (`bit_offset=10` in the `-d` output).

### 6.4 Summary of the pilot / RDS relationship

| Quantity                 | Known from the pilot? | How the decoder gets it               |
|--------------------------|-----------------------|---------------------------------------|
| 57 kHz carrier frequency | yes, exactly 3x       | `exp(-3j * pll)`                      |
| Carrier phase θ          | no, but it is constant | average of chip², angle / 2          |
| Carrier sign (±180°)     | no                    | not needed: differential coding       |
| Bit length               | yes, exactly 16 cycles | one chip per pilot cycle, 16 per bit |
| Bit start (1 of 16)      | no, but it is constant | best of 16 matched-filter averages   |

In short: the pilot gives us all the **rates** (frequency, bit length) exactly,
and turns the two **offsets** (carrier phase, bit start) into constants that
can be measured once by averaging, instead of being tracked all the time.

One consequence: a station that transmits in mono, without a pilot tone,
cannot be decoded by `fm_rds.py`, even if it does transmit RDS, because the PLL
has nothing to lock onto.

## 7. Differential decoding

Before the biphase step, the station encodes the data **differentially**:
a data `1` means "the level changes compared with the previous bit", and a `0`
means "the level stays the same".

```python
handle_bit(raw_bit ^ last_raw_bit)
```

The XOR is 1 when the current raw bit differs from the previous one. If the
whole signal were inverted (the 180-degree ambiguity of section 5.3), every
raw bit would be flipped, but the *changes* between bits would be exactly the
same, so the decoded data stays correct.

## 8. Finding blocks: the CRC

RDS data is organised in **blocks** of 26 bits: 16 bits of data plus a 10-bit
**checkword**. Four blocks, named A, B, C (or C') and D, form a **group**.

The checkword is a CRC (a kind of checksum) of the 16 data bits, with an extra
twist: it is XORed with an **offset word** that depends on the block position
(A, B, C, C' or D). So, when we divide the 26 received bits by the CRC
polynomial (`crc_remainder`), the remainder is not zero but equals the offset
word of that block. That tells us two things at once: the block is valid, and
which block it is.

`handle_bit` works like this:

- **Not synchronised yet:** after each new bit, the last 26 bits are tested.
  Most of the time the remainder matches nothing. When it matches one of the
  offset words, we have found where blocks begin, and which block that was.
- **Synchronised:** the remainder is checked only every 26 bits, and it must
  be the expected next block (A, then B, then C, then D, then A again...).
  Blocks that fail the check are discarded (`None`).
- After 10 bad blocks in a row, we assume synchronisation was lost and go back
  to searching bit by bit.

At the end of each group, the four blocks (some possibly `None`) are passed to
`handle_group`.

## 9. Understanding groups

Block B tells what type of group it is (0 to 15, version A or B). The decoder
understands these:

- **Every group, block A:** PI code, a 16-bit identifier of the station.
- **Every group, block B:** PTY, the program type (News, Pop music...).
- **Group 0A/0B:** two characters of the PS (station name, 8 characters)
  in block D; the station name arrives in four pieces.
- **Group 2A:** four characters of RadioText (up to 64 characters) in
  blocks C and D. **Group 2B:** two characters, in block D. A flag (A/B)
  toggles when the station starts a new text, so the old one is cleared.
- **Group 4A:** clock time: date (as a Modified Julian Day, converted to a
  calendar date) and UTC time, plus the local time offset.

Other group types are received (and counted as good blocks) but not interpreted.

## 10. The whole chain, in one picture

```
 fm1.py baseband (256k samples/s)
        |
        +--> band-pass 19 kHz --> PLL ----------------------+
        |                         (phase "pll", frequency)  |
        |                                                   | 3 x pll
        +--> band-pass 57 kHz --> multiply by e^(-j3·pll) <-+
                                        |
                                 sum over 1 pilot cycle = chip (19k/s)
                                        |
                                 rotate by -θ (θ from average of chip²)
                                        |
                                 matched filter over 16 chips
                                        |
                                 decide at best of 16 offsets = raw bit (1187.5/s)
                                        |
                                 differential decoding (XOR with previous)
                                        |
                                 CRC + offset words --> blocks A B C D
                                        |
                                 groups --> PI, PTY, PS, RadioText, clock
```
