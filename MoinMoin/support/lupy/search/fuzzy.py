# This module is part of the Lupy project and is Copyright 2005 Florian
# Festi. This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

from term import TermQuery
from boolean import BooleanScorer
from MoinMoin.support.lupy.index.term import Term

def min(*l):
    m = l[0]
    for v in l:
        if v<m: m = v
    return m

class FuzzyQuery(TermQuery):
    """Port of the Lucene FuzzyQuery
    Still untested, use on your own risk...
    """
    WORD_SIZE = 50

    def __init__(self, term, similarity, prefix_length):
        TermQuery.__init__(self, term)
        #self.term = term
        self.prefix = term.text()[:prefix_length]
        self.text = term.text()[len(self.prefix):]
        self.min_similarity = similarity
        self.d = []
        for i in xrange(self.WORD_SIZE):
            self.d.append([0]* self.WORD_SIZE) 

    def scorer(self, reader):
        prefix = self.prefix
        lprefix = len(prefix)
        field = self.term.field()
        terms = []
        
        ts = reader.terms(Term(field, self.prefix))
        scorer = BooleanScorer()

        while True:
            text = ts.term.text()
            if not text.startswith(prefix):
                break
            sim = self.similarity(text[lprefix:])
            if (ts.term.field()==field and
                sim > self.min_similarity):
                tq = TermQuery(ts.term)
                tq.weight=1.0
                scorer.add(tq.scorer(reader), False, False)
                terms.append(ts.term)
            try:
                ts.next()
            except StopIteration:
                break
            
        if terms is None:
            return None
        
        return scorer

    def initialize_array(self, n, m):
        d = self.d
        if len(d)<n+1:
            l = len(d[0])
            for i in xrange(len(d), n+1):
                d.append([0] * l)
        if len(d[0])<m+1:
            l = [0] * (m - len(d[0]) + 1)
            for i in xrange(len(d)):
                d[i].extend(l)

        for i in xrange(n+1): d[i][0] = i
        for i in xrange(m+1): d[0][i] = i
        

    def similarity(self, target):
        n = len(self.text)
        m = len(target)
        d = self.d

        self.initialize_array(n, m)

        for i in xrange(n):
            s_i = self.text[i]
            for j in xrange(m):
                if s_i != target[j]:
                    d[i+1][j+1] = min(d[i][j+1], d[i+1][j], d[i][j]) + 1
                else:
                    d[i+1][j+1] = min(d[i][j+1]+1, d[i+1][j]+1, d[i][j])
        return 1.0 - (d[n][m]/ float(len(self.prefix) + min(m,n)))

