# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

"""A simple interface to indexing and searching.
"""
import os, sys, re

from MoinMoin.support.lupy.index.indexwriter import IndexWriter
from MoinMoin.support.lupy.index.documentwriter import standardTokenizer
from MoinMoin.support.lupy.index.term import Term

from MoinMoin.support.lupy import document

from MoinMoin.support.lupy.search import indexsearcher
from MoinMoin.support.lupy.search.term import TermQuery
from MoinMoin.support.lupy.search.phrase import PhraseQuery
from MoinMoin.support.lupy.search.boolean import BooleanQuery


class Index:

    def __init__(self, name, create=False, analyzer=None):
        """
        @param name: Name of the directory for this index.
        @param create: Whether to create this directory or not.
        @type create: boolean
        """
        
        self.name = name
        self.analyzer = analyzer or standardTokenizer
        # Create the index if we need to. From here on we assume
        # that the index exists
        self.indexer = IndexWriter(self.name, create, analyzer)
        # Remember the default merge factor
        self.mergeFactor = self.indexer.mergeFactor
        # Clean up
        self.indexer.close()
        self.indexer = self.searcher = None
        
    def index(self, **kw):
        """Add a document to the index.
        
        **kw contains the name and values of each Field in the
        Document that we are creating.

        If the key in **kw starts with '_' the field will be created
        as a Keyword. If it starts with '__', it is created as a
        stored Text field (e.g. tokenized and stored), otherwise it
        will be created as a Text field. The leading '_' are removed
        before field creation.

        Text fields will have their value tokenized before
        indexing. The value is not stored in the index.  This is the
        usual type of field that you need for plain text.

        Keyword fields will not have their value tokenized.  The value
        is stored in the index and is returned with search hits on the
        Document. If you wanted to store the path to a document along
        with each document, you would use a Keyword field. The path
        would not be tokenized and its value would be returned in the
        query results, so you could easily open and display the file.
        """
        self._setupIndexer()
        
        # create document
        d = document.Document()

        # TODO - Please find another way of defining fields
        # than magic field names!!!

        # add a file field containing the path to this file
        for key, value in kw.items():
            if key[:2] == '__':
                key = key[2:]
                # Tokenized and stored
                f = document.Text(key, value, True)
            elif key[0] == '_':
                # Not tokenized and stored
                key = key[1:]
                # keyword
                f = document.Keyword(key, value)
            else:
                # Tokenized and not stored
                f = document.Text(key, value, False)
            d.add(f)
        self.indexer.addDocument(d)

    def _setupIndexer(self):
        if self.searcher is not None:
            self.searcher.close()
            self.searcher = None
        if self.indexer is None:
            self.indexer = IndexWriter(self.name, False, self.analyzer)
            self.indexer.mergeFactor = self.mergeFactor

    def _setupSearcher(self):
        if self.indexer is not None:
            self.indexer.close()
            self.indexer = None
        if self.searcher is None:
            self.searcher = indexsearcher.IndexSearcher(self.name)

    def delete(self, **kw):
        "Delete the first document containing the specified term. See also L{deleteAll}."
        # Not very efficient for bulk deletes
        # Use deleteAll for bulk deletes
        self._setupSearcher()
        if len(kw) != 1:
            raise RuntimeError, 'one and only one field for the moment'
        field, value = kw.items()[0]
        t = Term(field, value)
        self.searcher.reader.deleteTerm(t)
        
    def deleteAll(self, **kw):
        "Remove all documents containing this field and value."
        self.close()
        reader = indexsearcher.open(self.name)
        if len(kw) != 1:
            raise RuntimeError, 'one and only one field for the moment'
        field, values = kw.items()[0]
        for value in values:
            t = Term(field, value)
            reader.deleteTerm(t)
        # commit the deletes
        reader.close()

    def close(self):
        # Indexer and Searchers are different
        # and we have to open the right kind
        # for the operation we are performing.
        # The actual creation is done in the index and find
        # methods. Here we close whatever is open.
        if self.searcher is not None:
            self.searcher.close()
            self.searcher = None
        if self.indexer is not None:
            self.indexer.close()
            self.indexer = None

    def flush(self):
       """Flush outstanding indexes to disk.

       This makes sure we are searching the latest stuff.
       """
       if self.indexer is not None:
           self.indexer.flushRamSegments()

    def optimize(self):
        """Merge all on-disk segments into a single segment. Saves space and can speed up queries."""
        self._setupIndexer()
        self.indexer.optimize()

    def parse(self, field, qString):
        if qString.startswith('"'):
            qString = qString.strip('"')
            #qWords = qString.strip('"').split()
            qWords = self._tokenize(qString)
            return self.phraseSearch(field, qWords)
        else:
            qWords = self._tokenize(qString)
            if len(qWords) == 1:
                return self.termSearch(field, qWords[0])
            else:
                return self.boolSearch(field, qWords)

    def _tokenize(self, qString):
        return list(self.analyzer(qString))

    def find(self, qStr):
        """Perform a search in any field in this index.

        If the search string is enclosed in double quotes, a phrase
        search will be run; otherwise, the search will be for
        documents containing all words specified."""
        
        self._setupSearcher()
            
        fields = self.searcher.fieldNames()
        if not fields:
            return []
        all = [self.parse(field, qStr) for field in fields]
        if len(all) is 1:
            # simple case
            return self.searcher.search(all[0])
        
        q = BooleanQuery()
        for query in all:
            # OR all of the field queries
            q.add(query, False, False)
        hits = self.searcher.search(q)
        return hits

    def findInField(self, **kw):
        """Search only in a single field."""
        # eg index.findInField(text='flute')
        if len(kw) != 1:
            raise RuntimeError, 'one and only one field for the moment'
        self._setupSearcher()
        field, query = kw.items()[0]
        q = self.parse(field, query)
        hits = self.searcher.search(q)
        return hits
    
    def termSearch(self, field, term):
        "Search for a single C{term} in a C{field}."
        t = Term(field, term)
        q = TermQuery(t)
        return q

    def phraseSearch(self, field, words):
        "Search for a phrase (given as a list of words) in C{field}."
        q = PhraseQuery()
        for word in words:
            t = Term(field, word)
            q.add(t)  
        return q
            
    def boolSearch(self, field, ands=[], ors=[], nots=[]):
        """Build a simple boolean query.

        Each word in C{ands} is equiv to +word
        Each word in C{ors} is equiv to word
        Each word in C{nots} is equiv to -word

        E.g. C{boolSearch(['spam'], ['eggs'], ['parrot', 'cheese'])} is
        equiv to C{+spam eggs -parrot -cheese} in Google/Lucene syntax.
        """
        q = BooleanQuery()

        for a in ands:
            t = Term(field, a)
            tq = TermQuery(t)
            q.add(tq, True, False)
            
        for a in ors:
            t = Term(field, a)
            tq = TermQuery(t)
            q.add(tq, False, False)
            
        for a in nots:
            t = Term(field, a)
            tq = TermQuery(t)
            q.add(tq, False, True)
        
        return q
            
    def printHits(self, hits):
        if len(hits) == 0:
            print 'Nothing found!'
        else:
            for i in range(len(hits)):
                print hits.doc(i), hits.score(i)

    def setMergeFactor(self, anInt):
        "Set how many documents will be processed before the indexes will be merged. Never less than 2."
        # Never less than 2
        if anInt >= 2:
            self.mergeFactor = anInt
        
          
