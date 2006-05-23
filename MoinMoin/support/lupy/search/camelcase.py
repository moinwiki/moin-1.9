# This module is part of the Lupy project and is Copyright 2005 Florian
# Festi. This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

from term import TermQuery
from boolean import BooleanQuery, BooleanScorer
from phrase import PhraseQuery
from MoinMoin.support.lupy.index.term import Term

class CamelCaseQuery(TermQuery):
    """
    XXX write new comment
    A Query that matches documents that contains words
       the term starts with. This is usefull for CamelCase
       words. You need to filter the results to make shure
       the camel case words are really contained within the
       document.
    """
    def sumOfSquaredWeights(self, searcher):
        self.query = BooleanQuery()
        self.reader = searcher.reader
        self.splitToWords(self.term, self.reader, [])
        return self.query.sumOfSquaredWeights(searcher)

    def scorer(self, reader):
        return self.query.scorer(reader)
    
    def _add_phrase(self, terms):
        phrase = PhraseQuery()
        for term in terms:
            phrase.add(term)
        self.query.add(phrase, False, False)
        
    def splitToWords(self, term, reader, terms):
        text = term.text()
        field = term.field()
        for l in xrange(2, len(text)+1):
            prefix = text[:l]
            ts = reader.terms(Term(field, prefix))
            if ((ts.term.text()==prefix and
                ts.term.field()==field)):
                t = terms[:]
                t.append(ts.term)
                self.splitToWords(Term(field, text[l:]), reader, t)
        else:
            ts = reader.terms(term)

        # check for end words
        if len(text):
            return
            max_length = len(text) + 3
            while ts.term.text().startswith(text):
                if (len(ts.term.text()) < max_length and
                    ts.term.field()==field):
                    self._add_phrase(terms+[ts.term])
                try:
                    ts.next()
                except StopIteration:
                    break
        else:
            self._add_phrase(terms)
