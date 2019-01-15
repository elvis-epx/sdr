# Grey code generator
# http://www.finalcog.com/python-grey-code-algorithm

import math

def gray(i):
    """
    This function returns the i'th Gray Code.
    It is recursive and operates in O(log n) time.
    """
    if i == 0: return 0
    if i == 1: return 1

    ln2 = int(log2(i))
    # the grey code of index i is the same as the gray code of an index an 
    # equal distance on the other side of ln2-0.5, but with bit ln2 set
    pivot = 2**(ln2) - 0.5 # TODO: double everything so that we use no floats
    delta = i - pivot
    mirror = int(pivot - delta)
    x = gray(mirror)    # get the grey code of the 'mirror' value
    x = x + 2**(ln2)    # set the high bit
    return x


def log2(x):
    """
    Return log base 2 of x.
    """
    return math.log(x) / math.log(2)


def tcbin(x, y=8):
    """
    This function returns the padded, two's complement representation of x, in y-bits.
    It is conventional for y to be 8, 16, 32 or 64, though y can have any non-zero positive value. 
    """
    if x >= (2**(y - 1)) or x < -(2**(y - 1) or y < 1):
        raise Exception("Argument outside of range.")
    if x >= 0:
        binstr = bin(x)
        # pad with leading zeros
        while len(binstr) < y + 2:
            binstr = "0b0" + binstr[2:]
        return binstr
    return bin((2**y) + x) # x is negative
 
