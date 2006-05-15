# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

class Hits(object):
    """A ranked list of documents, used to hold search results."""
    def __init__(self, s, q, f):
        """Initialize scoreDocs and totalHits.
        """
        self.query = q
        self.searcher = s
        self.filter = f
        self.hitDocs = []
        self._cache = []
        self.maxDocs = 200
        self.length = 0
        # retrieve 100 initially
        self.getMoreDocs(50)        
        
    def __len__(self):
        return self.length

    def __getitem__(self, indexOrSlice):
        # NB - Does not handle hits[:-1]
        # there has to be a better way than isinstance
        if isinstance(indexOrSlice, int):
            return self.doc(indexOrSlice)
        else:
            slyce = indexOrSlice
            start = slyce.start or 0
            stop = min(slyce.stop or len(self), len(self))
            step = slyce.step or 1
            return [self[i] for i in range(start, stop, step)] 
            
    def doc(self, n):
        if n > len(self.hitDocs):
            self.getMoreDocs(n)
        elif n >= self.length:
            raise IndexError, 'Not a valid hit number ' + str(n)
        hitDoc = self.hitDocs[n]
        
        # update LRU cache of documents
        # remove from list, if there
        if hitDoc in self._cache:
            self._cache.remove(hitDoc)
        # add to front of list
        self._cache.insert(0,hitDoc)

        if len(self._cache) > self.maxDocs:
            oldLast = self._cache[-1]
            del self._cache[-1]
            # let doc get gc'd
            oldLast['doc'] = None

        if hitDoc['doc'] is None:
            # cache miss: read document
            hitDoc['doc'] = self.searcher.doc(hitDoc['id'])

        return hitDoc['doc']

    def getMoreDocs(self, minDoc):
        """Tries to add new documents to hitDocs.
        Ensures that the hit numbered C{minDoc} has been retrieved.
        """
        minDoc = max(len(self.hitDocs), minDoc)
        
        # double number retrieved
        n = minDoc * 2
        
        topDocs = self.searcher.search(self.query, self.filter, n)
        scoreDocs = topDocs.scoreDocs
        self.length = topDocs.totalHits
        
        scoreNorm = 1.0
        if self.length > 0 and scoreDocs[0].score > 1.0:
            scoreNorm  = 1.0 / scoreDocs[0].score
            
        if len(scoreDocs) < self.length:
            end = len(scoreDocs)
        else:
            end = self.length
            
        for i in range(len(self.hitDocs),end):
            self.hitDocs.append({'score': scoreDocs[i].score * scoreNorm, 'id': scoreDocs[i].doc, 'doc': None})
                
    def score(self, n):
        """ Returns the score for the C{n}th document in the set.
        """
        return self.hitDocs[n]['score']

    def __repr__(self):
        s=  '<' + str(len(self)) + ' Hit'
        if len(self) == 1:
            s += '>'
        else:
            s += 's>'
        return s
