# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

import math, itertools

import similarity, hits

from bisect import insort
from MoinMoin.support.lupy.index import segment, segmentmerger
from MoinMoin.support.lupy import store

def openDir(directory):
    infos = segment.SegmentInfos()
    infos.read(directory)
    if len(infos) == 1:       # index is optimized
        return segmentmerger.SegmentReader(infos[0], True)
    elif len(infos) == 0:
        readers = []
    else:
        readers = [segmentmerger.SegmentReader(info,False) for info in infos[:-1]]
        readers.append(segmentmerger.SegmentReader(infos[-1],True))
    return segmentmerger.SegmentsReader(directory, readers)

def open(path):
    """Returns an IndexReader reading the index in an FSDirectory in
    the named path."""

    return openDir(store.getDirectory(path, False))


class IndexSearcher:

    """The base class for search implementations.
    Implements search over a single index.
    
    Subclasses may implement search over multiple indices, and over
    indices on remote servers."""
    
    def __init__(self, dirOrPath):
        """Creates a searcher searching the provided index.
        """
        if isinstance(dirOrPath, basestring):
            self.reader = open(dirOrPath)
        else:
            self.reader = openDir(dirOrPath)
        
    def close(self):
        """Frees resources associated with this Searcher."""
        self.reader.close()

    def docFreq(self, term):
        return self.reader.docFreq(term)

    def maxDoc(self):
        return self.reader.maxDoc()

    def doc(self, i):
        """For use by L{lupy.search.hits.Hits}."""
        return self.reader.document(i)

    def searchAll(self, query, filter):
        """Lower-level search API.

        Returns a generator that yields all non-zero scoring documents
        for this query that pass the filter.

        Applications should only use this if they need I{all} of the
        matching documents.  The high-level search API
        (L{search(Query)}) is usually more efficient, as it skips
        non-high-scoring hits.

         - C{query} to match documents
         - C{filter} if non-null, a bitset used to eliminate some documents
        """
        scorer = getScorer(query, self, self.reader)
        if filter is not None:
            bits = filter.bits(reader)

        if scorer is None:
            return
        
        return itertools.imap(lambda doc, score: doc,
                              itertools.ifilter(lambda doc, score: score > 0 and (bits is None or bits.get(doc)),
                                                scorer.score(self.reader.maxDoc())))
            
    def search(self, query, filter=None, nDocs=None):
        
        """Search this index for documents matching C{query} and
        (optionally) passing the C{filter} bitvector. If C{nDocs} is
        specified then only the top C{nDocs} hits will be returned."""
        
        if nDocs is None:
            return hits.Hits(self, query, filter)
        
        scorer = getScorer(query, self, self.reader)
        if scorer is None:
            return TopDocs(0, [])

        if filter is not None:
            bits = filter.bits(reader)
        else:
            bits = None

        scoreDocs = []
        totalHits = [0]
        minScore = 0.0

        for doc, scr in scorer.score(self.reader.maxDoc()):        
            if scr > 0.0 and (bits is None or bits.get(doc)):
                # ignore zeroed buckets and docs not in bits
                totalHits[0] += 1
                if scr >= minScore:
                    # update hit queue
                    insort(scoreDocs, ScoreDoc(doc, scr))
                    if len(scoreDocs) > nDocs:
                        # if hit queue overfull
                        # remove lowest in hit queue
                        scoreDocs.pop()
                        # reset minimum score
                        minScore = scoreDocs[0].score
                
        return TopDocs(totalHits[0], scoreDocs)

    def fieldNames(self):
        # Experimental for auto queries
        return self.reader.fieldNames()


def getScorer(query, searcher, reader):
    sum = query.sumOfSquaredWeights(searcher)
    norm = 1.0/(math.sqrt(sum) or 1.0)
    query.normalize(norm)
    return query.scorer(reader)

class ScoreDoc(object):
  
    def __init__(self, d, s):
        self.doc = d
        self.score = s

    def __lt__(a, b):
        if a.score == b.score:
            return a.doc > b.doc
        else:
            return a.score < b.score


class TopDocs(object):

    def __init__(self, th, sds):
        self.totalHits = th
        self.scoreDocs = sds
        
