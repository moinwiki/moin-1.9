# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

import itertools
import similarity
import traceback

class BooleanQuery:
    """A Query that matches documents matching boolean combinations of
    other queries, typically L{lupy.search.term.TermQuery}s or L{lupy.search.phrase.PhraseQuery}s."""
    

    def __init__(self):
        """Constructs an empty boolean query."""
        
        self.clauses = []
        self.boost = 1.0

    def addClause(self, clause):
        """Adds a BooleanClause to this query."""
        self.clauses.append(clause)


    def add(self, query, required, prohibited):
        """Adds a clause to a boolean query.  Clauses may be:
        C{required} which means that documents which I{do not}
        match this sub-query will I{not} match the boolean query;
        C{prohibited} which means that documents which I{do}
        match this sub-query will I{not} match the boolean query; or
        neither, in which case matched documents are neither prohibited from
        nor required to match the sub-query.
        
        It is an error to specify a clause as both C{required} and
        C{prohibited}."""
        
        self.clauses.append(BooleanClause(query,
                                          required,
                                          prohibited))
        

    def normalize(self, norm):
        for c in self.clauses:
            if not c.prohibited:
                c.query.normalize(norm)

    def scorer(self, reader):
        # optimize zero-term case
        if len(self.clauses) == 1:
            # just return term scorer
            c = self.clauses[0]
            if not c.prohibited:
                return c.query.scorer(reader)

        result = BooleanScorer()

        for c in self.clauses:
            subScorer = c.query.scorer(reader)
            if subScorer is not None:
                result.add(subScorer, c.required, c.prohibited)
            elif c.required:
                return None

        return result
            

    def sumOfSquaredWeights(self, searcher):
        sum = 0.0
        
        for c in self.clauses:
            if not c.prohibited:
                # sum sub-query weights
                sum += c.query.sumOfSquaredWeights(searcher)
            else:
                # allow complex queries to initialize themself
                c.query.sumOfSquaredWeights(searcher)
        return sum


    def toString(self, field):
        """Prints a user-readable version of this query"""

        buffer = ''

        for c in self.clauses:
            if c.prohibited:
                buffer += '-'
            elif c.required:
                buffer += '+'

            subQuery = c.query
            if isinstance(subQuery, BooleanQuery):
                # wrap sub-bools in parens
                buffer += '('
                buffer += c.query.toString(field)
                buffer += ')'
            else:
                buffer += c.query.toString(field)
            
        return buffer
 
class BooleanClause(object):
    """A clause in a BooleanQuery"""

    def __init__(self, q, r, p):
        self.query = q
        self.required = r
        self.prohibited = p
    
class BooleanScorer:
    
    def __init__(self):
        self.coordFactors = None
        self.maxCoord = 1
        self.nextMask = 1
        self.prohibitedMask = 0
        self.requiredMask = 0
        self.scorers = []        
        self.currentDoc = 0
        self.validList = []
        self.table = {}
        
    def add(self, scorer, required, prohibited):
        mask = 0
        if required or prohibited:
            if self.nextMask == 0:
                raise Exception, 'More than 32 required/prohibited clauses in a query.'
            mask = self.nextMask
            self.nextMask = self.nextMask << 1
        else:
            '???'
            mask = 0
            
        if not prohibited:
            self.maxCoord += 1
            
        if prohibited:
            # Update prohibited mask
            self.prohibitedMask |= mask
        elif required:
            # Update required mask
            self.requiredMask |= mask
            
        self.scorers.append(SubScorer(scorer, required, prohibited, mask))
        
        
    def computeCoordFactors(self):
        self.coordFactors = []
        for i in range(self.maxCoord):
            self.coordFactors.append(similarity.coord(i, self.maxCoord))
            

    def collect(self, doc, score, mask):
        bucket = self.table.get(doc, None)
        if bucket is None:
            #doc, score, bits, coord
            bucket = [-1, 0, 0, 0]
            self.table[doc] = bucket            
        if bucket[0] != doc:
            # invalid doc
            # initialize fields
            bucket[:] = [doc, score, mask, 1]            
            self.validList.append(bucket)
        else:
            # valid bucket
            # increment score
            bucket[1] += score
            # add bits in mask
            bucket[2] |= mask
            # increment coord
            bucket[3] += 1 # XXX
            #print doc, score, mask, bucket

            
    def score(self, maxDoc):
        if self.coordFactors is None:
            self.computeCoordFactors()
        for t in self.scorers:
            #print "SCORER %r" % t.scorer
            for d,score in t.scorer.score(maxDoc):
                #print "DOCUMENT %r %r" % (d, score)
                self.collect(d,score,t.mask)
        return self.collectHits()
    
    def collectHits(self):        
        for bucket in self.validList:
            doc, score, bits, coord = bucket
            if (bits & self.prohibitedMask) == 0 and (bits & self.requiredMask) == self.requiredMask:
                # if prohibited and required check out
                # add to results
                #print "CollectHits:", doc, score, self.coordFactors, coord
                try:
                    scorecf = score * self.coordFactors[coord]
                except IndexError, err: # XXX ugly way to avoid it crashing 8(
                    scorecf = 0.0
                yield (doc, scorecf)
        del self.validList[:]
            
                
class SubScorer(object):
    
    def __init__(self, scorer, required, prohibited, mask):
      self.scorer = scorer
      self.required = required
      self.prohibited = prohibited
      self.mask = mask
    
    
    
    
