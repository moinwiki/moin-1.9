# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

import math


NORM_TABLE = map(lambda x: x/255.0, range(0,256))

def coord(overlap, maxOverlap):
    return overlap/float(maxOverlap)

def idf(docFreq, numDocs):
    return math.log((numDocs/(docFreq + 1.0)) or 1.0) + 1.0

def idfTerm(term, searcher):
    """Use maxDoc() instead of numDocs() because its proportional to docFreq(),
    i.e., when one is inaccurate, so is the other, and in the same way."""

    return idf(searcher.docFreq(term), searcher.maxDoc())

def normByte(normByte):
    """Un-scales from the byte encoding of a norm into a float, i.e.,
    approximately 1/sqrt(numTerms)."""

    return NORM_TABLE[normByte & 0xFF]

def normInt(numTerms):
    """Computes the normalization byte for a document given the total number of
    terms contained in the document.  These values are stored in an index and
    used by the search code

    Scales 1/sqrt(numTerms) into a byte, i.e. 256/sqrt(numTerms).
    Math.ceil is used to ensure that even very long documents don't get a
    zero norm byte, as that is reserved for zero-lengthed documents and
    deleted documents."""

    if numTerms == 0:
        return 0
    return int((math.ceil(255.0 / math.sqrt(numTerms)))) & 0xFF


def tf(freq):
    return float(math.sqrt(freq))


