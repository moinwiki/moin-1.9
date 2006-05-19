# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

from array import array
import os

# Table of bits/byte
BYTE_COUNTS = array('B',[
    0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4,
    1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
    1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
    2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
    1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
    2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
    2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
    3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
    1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
    2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
    2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
    3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
    2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
    3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
    3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
    4, 5, 5, 6, 5, 6, 6, 7, 5, 6, 6, 7, 6, 7, 7, 8])

class BitVector(object):

    def __init__(self, dirOrInt, name = None):
        # some low fi type dispatch
        if name is None:
            # create a new vector of dirOrInt length
            self.len = dirOrInt
            self.bits = array('B', ([0x00]*((self.len >> 3) + 1)))
            self.bcount = -1
        else:
            # read a BitVector from a file
            input = dirOrInt.openFile(name)
            try:
                self.len = input.readInt()      # read size
                self.bcount = input.readInt()          # read count
                self.bits = array('B', [0x00]*((self.len >> 3) + 1)) # allocate bits
                input.readBytes(self.bits, 0, len(self.bits))
            finally:
                input.close()
            

    def init__(self, n):
        self.len = n
        self.bits = array('B', ([0x00]*((self.len >> 3) + 1)))


    def clear(self, bit):
        # Set value of bit to zero
        self.bits[bit >> 3] &= ~(1 << (bit & 7))
        self.bcount = -1


    def count(self):
        """Returns the total number of one bits in this vector.
        This is efficiently computed and cached, so that, if the
        vector is not changed, no recomputation is done for
        repeated calls."""

        if self.bcount == -1:
            c = 0
            for b in self.bits:
                c += BYTE_COUNTS[b & 0xFF]    # sum bits per byte

            self.bcount = c

        return self.bcount


    def get(self, bit):
        # Returns True if bit is one and False if it is zero
        return(self.bits[bit >> 3] & (1 << (bit & 7)) != 0)
    

    def set(self, bit):
        # Sets the value of bit to one
        self.bits[bit >> 3] |= 1 << (bit & 7)
        self.bcount = -1

        
    def __len__(self):
        return self.len


    def write(self, d, name):
        output = d.createFile(name)
        try:
            output.writeInt(len(self))    # write size
            output.writeInt(self.count())   # write count
            output.writeBytes(self.bits, len(self.bits))
        finally:
            output.close()
            
def sibpath(path, sibling):
    """Return the path to a sibling of a file in the filesystem.

    This is useful in conjunction with the special __file__ attribute
    that Python provides for modules, so modules can load associated
    resource files.
    """
    return os.path.join(os.path.dirname(os.path.abspath(path)), sibling)

