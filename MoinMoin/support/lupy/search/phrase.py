# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.


from bisect import insort
from MoinMoin.support.lupy.search import term, similarity
import sys

class PhraseQuery:
    """A query that matches documents containing a particular
    sequence of terms. This may be combined with other terms
    with a L{lupy.search.boolean.BooleanQuery}.
    """

    def __init__(self):
        """Constructs an empty phrase query."""
        
        self.idf = 0.0
        self.slop = 0
        self.terms = []
        self.weight = 0.0
        self.boost = 1.0

    def add(self, term):
        """Adds a term to the end of the query phrase."""
        if len(self.terms) == 0:
            self.field = term.field()

        elif term.field() != self.field:
            raise Exception, 'All phrase terms must be in the same field: ' + str(term)

        self.terms.append(term)


    def getSlop(self):
        """Returns the slop.  See setSlop()."""
        return self.slop


    def normalize(self, norm):
        # normalize for query
        self.weight *= norm
        # factor from document
        self.weight *= self.idf


    def scorer(self, reader):
        # optimize zero-term case
        if len(self.terms) == 0:
            return None

        # optimize one-term case
        if len(self.terms) == 1:
            t = self.terms[0]
            docs = reader.termDocsTerm(t)
            if docs is None:
                return None
            return term.TermScorer(docs, reader.normsField(t.field()), self.weight)

        tps = [] 
        
        for t in self.terms:
            p = reader.termPositionsTerm(t)
            if p is None:
                # I am not sure how this is ever reached?
                return None
            tps.append(p)

        if self.slop == 0:
            return ExactPhraseScorer(tps, reader.normsField(self.field),
                                     self.weight)
        else:
            return SloppyPhraseScorer(tps, reader.norms(self.field),
                                      self.weight)


    def sumOfSquaredWeights(self, searcher):
        # sum term IDFs
        for term in self.terms:
            self.idf += similarity.idfTerm(term, searcher)
            
        self.weight = self.idf * self.boost
        # square term weights
        return self.weight * self.weight


    def toString(self, f):
        """Prints a user-readable version of this query"""

        buffer = ''
        if not self.field == f :
            buffer += f + ':'
        buffer += '\\'

        for term in self.terms[:-1]:
            buffer += term.text() + ' '
            
        buffer += self.terms[-1].text() + '\\'

        if self.slop != 0:
            buffer += '~' + str(self.slop)

        if self.boost != 1.0:
            buffer += '^' + str(self.boost)

        return buffer


class PhraseScorer:
    
    def __init__(self, tps, n, w):
        self.norms = n
        self.weight = w
        
        self.pps = [PhrasePositions(tp, i) for i, tp in enumerate(tps)]
        self.pps.sort()
                        
    def phraseQuery(self):
        """Subclass responsibility"""

    def score(self, end):
        # find doc w/ all the terms
        while self.pps[-1].doc < end:
            while self.pps[0].doc < self.pps[-1].doc:
                self.pps[0].advance()
                while self.pps[0].doc < self.pps[-1].doc:
                    self.pps[0].advance()
                self.pps.append(self.pps.pop(0))
                if self.pps[-1].doc >= end:
                    return
                
            # found doc with all terms
            # check for phrase
            freq = self.phraseFreq()
            
            if freq > 0.0:
                # compute score
                score = similarity.tf(freq) * self.weight
                # normalize
                score *= similarity.normByte(self.norms[self.pps[0].doc])
                # add to results
                yield (self.pps[0].doc, score)
            # resume scanning
            self.pps[-1].advance()
                
                
        

class ExactPhraseScorer(PhraseScorer):
    
    def phraseFreq(self):
        for pp in self.pps:
            pp.firstPosition()
        self.pps.sort()
        freq = 0.0
        
        init = 0
        # the 'init' bits are to simulate a do-while loop :-/
        while init == 0 or self.pps[-1].nextPosition():
            while self.pps[0].position < self.pps[-1].position:
                # scan forward in first
                init2 = 0
                while init2 == 0 or self.pps[0].position < self.pps[-1].position:
                    if not self.pps[0].nextPosition():
                        return freq
                    init2 = 1
                    
                self.pps.append(self.pps.pop(0))
            # all equal: a match
            freq += 1
            init = 1
            
        return freq
        

class PhrasePositions(object):

    def __init__(self, t, o):
        self.tp = t
        self.offset = o
        
        self.position = 0
        self.count = 0
        self.doc = 0
        self.tpiter = iter(t)
        self.advance()
        
        
    def firstPosition(self):
        self.count = self.tp.frq
        self.nextPosition()
        
        
    def advance(self):
        """Increments to next doc"""
        
        for doc, frq, nextPos in self.tpiter:
            self.doc = doc
            self.frq = frq
            self._nextPos = nextPos
            self.position = 0
            return
        else:
            # close stream
            self.tp.close()
            # sentinel value
            self.doc = sys.maxint
            return
        
        
    def nextPosition(self):
        if self.count > 0:
            self.count -= 1
            # read subsequent positions
            self.position = self._nextPos.next() - self.offset
            return True
        else:
            self.count -= 1
            return False
        
                
    def __repr__(self):
        res = '<pp>d:' + str(self.doc) + ' p:' + str(self.position) + ' o:' + str(self.offset)
        return res

    def __lt__(this, that):
        if this.doc == that.doc:
            return this.position < that.position
        else:
            return this.doc < that.doc
