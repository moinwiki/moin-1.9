# Binary patching and diffing
#
# Copyright 2005 Matt Mackall <mpm@selenic.com>
# Copyright 2006 MoinMoin:AlexanderSchremmer
#
# Algorithm taken from mercurial's mdiff.py
#
# This software may be used and distributed according to the terms
# of the GNU General Public License, incorporated herein by reference.

import zlib, difflib, struct

BDIFF_PATT = ">lll"

def compress(text):
    return zlib.compress(text) # here we could tune the compression level

def decompress(bin):
    return zlib.decompress(bin)

def diff(a, b):
    """ Generates a binary diff of the passed strings. """
    if not a:
        return b and (struct.pack(BDIFF_PATT, 0, 0, len(b)) + b)

    bin = []
    la = lb = 0
    
    p = [0]
    for i in a: p.append(p[-1] + len(i))
    
    for am, bm, size in difflib.SequenceMatcher(None, a, b).get_matching_blocks():
        s = "".join(b[lb:bm])
        if am > la or s:
            bin.append(struct.pack(BDIFF_PATT, p[la], p[am], len(s)) + s)
        la = am + size
        lb = bm + size
    
    return "".join(bin)

def patchtext(bin):
    """ Returns the new hunks that are contained in a binary diff."""
    pos = 0
    t = []
    while pos < len(bin):
        p1, p2, l = struct.unpack(BDIFF_PATT, bin[pos:pos + 12])
        pos += 12
        t.append(bin[pos:pos + l])
        pos += l
    return "".join(t)

def patch(a, bin):
    """ Patches the string a with the binary patch bin. """
    c = last = pos = 0
    r = []

    while pos < len(bin):
        p1, p2, l = struct.unpack(BDIFF_PATT, bin[pos:pos + 12])
        pos += 12
        r.append(a[last:p1])
        r.append(bin[pos:pos + l])
        pos += l
        last = p2
        c += 1
    r.append(a[last:])

    return "".join(r)

def test():
    a = "föo" * 30
    b = "bär" * 30
    d = diff(a, b)
    z = compress(d)
    print `patchtext(d)`
    #print `d`
    print b == patch(a, d)
    print len(d), len(z)

test()