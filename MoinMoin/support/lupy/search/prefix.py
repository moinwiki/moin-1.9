# This module is part of the Lupy project and is Copyright 2005 Florian
# Festi. This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

from term import TermQuery
from boolean import BooleanQuery
from MoinMoin.support.lupy.index.term import Term

class PrefixQuery(TermQuery):
    """A Query that matches documents that contains the term and terms
    that start with the term and have upto max_addon additional chars.
    This allows to have better matching especially if no stemming is used"""
    def __init__(self, term, max_addon=10000):
        TermQuery.__init__(self, term)
        self.term = term
        self.max_length = len(term.text()) + max_addon
        self.weight = 0.0
        self.boost = 1.0
                        
    def sumOfSquaredWeights(self, searcher):
        self.query = BooleanQuery()
        reader = searcher.reader

        text = self.term.text()
        field = self.term.field()

        ts = reader.terms(self.term)

        while True:
            if not ts.term.text().startswith(text):
                break
            if ((len(ts.term.text()) <= self.max_length) and
                ts.term.field()==field):
                self.query.add(TermQuery(ts.term), False, False)
            try:
                ts.next()
            except StopIteration:
                break

        return  self.query.sumOfSquaredWeights(searcher)

    def scorer(self, reader):
        return self.query.scorer(reader)
