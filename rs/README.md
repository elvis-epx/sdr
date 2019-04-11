# Decimal Reed-Solomon implementation

This is a proof-of-concept implementation of Reed-Solomon for decimal numbers,
based on the original article. It generates check digits, just like a modulo-11
checkdigit, but it is also capable of correcting errors.

It is not perfect but does its job most of the time and is a good tutorial to the
RS algorithm. It can also be used as a simple checkdigit generator and error
detection device.

## How to use

Reed-Solomon works with fixed message sizes. The code tries to be somewhat tolerant
on messages with unexpected size or type i.e. it tries to pad with zeros and/or
convert to string when necessary.

````
>>> from decimalrs import DecimalRS
>>> rs = DecimalRS(7, False)
>>> rs.encode(3141592)
'3141592134'
>>> rs.decode("3141592134")
(3141592, 0)                      # message was intact
>>> rs.decode("3141593134")
(3141592, 2)                      # message was corrupted, corrected
>>> rs.decode("3141593334")
(None, 4)                         # uncorrectable message
````

Reed-Solomon needs a prime or power-of-prime field, so the checkdigits are actually
GF(11), meaning there can be an "X" to represent the eleventh symbol. The decode()
argument must therefore be a string.

````
rs.encode(4)
'000000485X'
rs.decode('485X')
>>> rs.decode('485X')
(4, 0)                            # intact message
>>> rs.decode('4852')
(4, 1)                            # checkdigit corrupted, corrected
````

If you simply can't deal with "X" checkdigits, you can use the class in 
"weakened mode" which casts "X" to zero. The error handling powers are
reduced. In this mode, decode() accepts an integer argument.

````
>>> rsw = DecimalRS(7, True)
>>> rsw.encode(4)
'0000004850'
>>> rsw.decode(4855)
(4, 3)                           # corrected, error was *probably* in 
                                 # checkdigit but certaintly is lower
>>> rsw.decode(4865)
(None, 4)                        # uncorrectable
>>> rsw.decode(4850)
(4, 0)                           # message intact
>>> rsw.decode(5850)
(4, 2)                           # corrected
````

For more examples, check the unit-test code within the module itself
(the code after the idiom `` __name__ == '__main__'``).

## Limitations

The Reed-Solomon algorithm handles only fixed-size messages whose length must
be smaller than group size. Since our implementation uses GF(11) and three
checkdigits, the maximum net length is 7 digits.

In principle, 3 checkdigits guarantee the detection of every 2-digit
corruption, and correction for every 1-digit corruption. For 3-digit
errors, there is a small probability (~5%) of taking the message as
correctable when it is no thte case. For 4-digit errors and beyond,
this probability is ~7%.

Probably due to characteristics of GF(11) field, there are some 'birdies',
that is, messages with 2 corrupted digits that fool the algorithm and
pass off as correctable, breaking the original promise of detecting every
two-digit error. The probability of finding such a 'birdie' is about 1%.

For the weakened version ("X" checkdigits cast as zeroes) the numbers are
much worse. The probability of taking a corrupted multiple-error
message as good rises to ~10%, and the proportion of 'birdies' rise to
~4%. Also, there is a 0.6% chance of wrongful correction of one-digit
errors (i.e. the message is corrected but the result is not equal to the
original).

(These percentages above can be checked by running the included scripts test.py
and test2.py.)
