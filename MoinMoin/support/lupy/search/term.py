# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

from itertools import islice
import sys
import similarity

class TermQuery:
    """A Query that matches documents containing a term.
    This may be combined with other terms with a L{lupy.search.boolean.BooleanQuery}."""

    def __init__(self, t):
        """Constructs a query for the term B{t}."""
        
        self.term = t
        self.idf = 0.0
        self.weight = 0.0
        self.boost = 1.0

    def normalize(self, norm):
        # normalize for query
        self.weight *= norm
        # factor from document
        self.weight *= self.idf
        
        
    def scorer(self, reader):
        termDocs = reader.termDocsTerm(self.term)
        if termDocs is None:
            return None
        
        return TermScorer(termDocs,
                          reader.normsField(self.term.field()),
                          self.weight)
    

    def sumOfSquaredWeights(self, searcher):
        self.idf = similarity.idfTerm(self.term, searcher)
        self.weight = self.idf * self.boost
        # square term weights
        return self.weight * self.weight


    def toString(self, field):
        """Prints a user-readable version of this query"""

        buffer = ''
        if not self.term.field() == field:
            buffer += self.term.field() + ':'

        buffer += self.term.text()

        if self.boost != 1.0:
            buffer += '^' + str(self.boost)

        return buffer
    
    

class TermScorer:

    """Scorer for L{TermQuery}s."""

    SCORE_CACHE_SIZE = 32


    def __init__(self, td, n, w):
        self.termDocs = td
        self.norms = n
        self.weight = w
        self.scoreCache = [similarity.tf(i) * self.weight for i in range(self.SCORE_CACHE_SIZE)]
        #self.docs, self.freqs = zip(*list(islice(self.termDocs, 128)))
        
    def score(self, end):
        
        for d, f in self.termDocs.read():
            if d >= end:
                break
            if f < self.SCORE_CACHE_SIZE:
                score = self.scoreCache[f]
            else:
                # cache miss
                score = similarity.tf(f) * self.weight

            # normalize for field
            score *= similarity.normByte(self.norms[d])
            # collect score
            yield (d, score)
        else:
            # close stream
            self.termDocs.close()
            # set to sentinel value
            self.doc = sys.maxint

