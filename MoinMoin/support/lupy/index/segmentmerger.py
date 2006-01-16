# -*- test-case-name: lupy.test -*-
# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

import sys

from array import array

from  MoinMoin.support.lupy.util import BitVector

from MoinMoin.support.lupy.index import field, term, segment

#import copy #broken, see comments at top of this file:
from MoinMoin.support import copy

from bisect import insort
import os

class IndexReader(object):
    
    """IndexReader is an abstract class, providing an interface for
    accessing an index. Search of an index is done entirely through this abstract
    interface, so that any subclass which implements it is searchable.

    Concrete subclasses of IndexReader are usually constructed with a call to L{lupy.search.indexsearcher.open}C{(path)}.

    For efficiency, in this API documents are often referred to via document
    numbers, non-negative integers which each name a unique document in the index.
    These document numbers are ephemeral--they may change as documents are added
    to and deleted from an index. Clients should thus not rely on a given document
    having the same number between sessions. """

    def __init__(self, d):
        self.directory = d

    def indexExists(self, d):
        """Returns True if an index exists at the specified directory."""
        return self.directory.fileExists('segments')

    def isLocked(self):
        # return self.directory.fileExists('write.lock')
        return False

    def lastModified(self, d):
        """Returns the time the index in this directory was last modified."""
        return self.directory.fileModified('segments')
    
    def lastModifiedString(self, d):
        return self.lastModified(d)
    

    #def unlock(self, directory):
    #    """Forcibly unlocks the index in the named directory.
    #    
    #    Caution: this should only be used by failure recovery code,
    #    when it is known that no other process nor thread is in fact
    #    currently accessing this index."""
    #    
    #    directory.deleteFile('write.lock')
    #    directory.deleteFile('commit.lock')
        

    def close(self):
        """Closes files associated with this index.
        Also saves any new deletions to disk.
        No other methods should be called after this has been called."""
        
        self.doClose()
        

    def doClose(self):
        pass


    def delete(self, docNum):
        
        """Deletes the document numbered C{docNum}.  Once a document
        is deleted it will not appear in TermDocs or TermPositions
        enumerations.  Attempts to read its field with the L{document}
        method will result in an error.  The presence of this document
        may still be reflected in the C{docFreq} statistic, though
        this will be corrected eventually as the index is further
        modified.  """
        self.doDelete(docNum)
        

    def deleteTerm(self, term):
        """ Deletes all documents containing C{term}.
        This is useful if one uses a document field to hold a unique ID string for
        the document.  Then to delete such a document, one merely constructs a
        term with the appropriate field and the unique ID string as its text and
        passes it to this method.  Returns the number of documents deleted.
        """
        docs = self.termDocsTerm(term)
        try:        
            return len([self.delete(doc) for doc,freq in docs])
        finally:
            docs.close()

    
    
    def termDocs(self):
        """Returns an unpositioned TermDocs enumerator.
        """
    
    
    def termDocsTerm(self, term):
        """ Returns an enumeration of all the documents which contain
        C{term}. For each document, the document number, the frequency of
        the term in that document is also provided, for use in search scoring.
        Thus, this method implements the mapping:

        Term &nbsp;&nbsp; S{->} <docNum, freq>*

        The enumeration is ordered by document number.  Each document number
        is greater than all that precede it in the enumeration."""
        
        termDocs = self.termDocs()
        termDocs.seekTerm(term)
        return termDocs
    
    
    def termPositionsTerm(self, term):

        """Returns an enumeration of all the documents which contain
        C{term}.  For each document, in addition to the document
        number and frequency of the term in that document, a list of
        all of the ordinal positions of the term in the document is
        available.  Thus, this method implements the mapping:
    
        M{Term S{->} <docNum, freq, <pos(1), pos(2), ... , pos(freq-1)>>*}

        This positional information faciliates phrase and proximity searching.
        
        The enumeration is ordered by document number.  Each document
        number is greater than all that precede it in the
        enumeration."""
        
        termPositions = self.termPositions()
        termPositions.seekTerm(term)
        return termPositions
        
class SegmentTermDocs(object):
    
    def __init__(self, parent):
        self.parent = parent
        self.freqStream = parent.freqStream.clone()
        self.deletedDocs = parent.deletedDocs

        self.docu = 0
        self.frq = 0
        
    def close(self):
        self.freqStream.close()

    def __iter__(self):
        return self

    def next(self):
        while True:
            if self.freqCount == 0:
                raise StopIteration
            
            docCode = self.freqStream.readVInt()
            self.docu += docCode >> 1
            if (docCode & 1):
                self.frq = 1
            else:
                self.frq = self.freqStream.readVInt()

            self.freqCount -= 1
            
            if self.deletedDocs is None or (not self.deletedDocs.get(self.docu)):
                return self.docu, self.frq
            self.skippingDoc()
            

    def read(self):
        return list(self)

    def skippingDoc(self):
        pass

    def seekTerm(self, term):
        ti = self.parent.tis.getTerm(term)
        self.seekTi(ti)


    def seekTi(self, ti):
        if ti is None:
            self.freqCount = 0
        else:
            self.freqCount = ti.docFreq
            self.docu = 0
            self.freqStream.seek(ti.freqPointer)
            

class SegmentTermPositions(SegmentTermDocs):

    def __init__(self, p):
        self.proxCount = 0
        self.position = 0
        SegmentTermDocs.__init__(self, p)

        self.proxStream = self.parent.proxStream.clone()

    def close(self):
        SegmentTermDocs.close(self)
        self.proxStream.close()


    def next(self):
        #generator for accessing positions in the current doc
        #kinda lame since it utterly breaks after next iteration
        def nextPosition(freq):
            for i in range(freq):
                self.proxCount -= 1
                self.position += self.proxStream.readVInt()
                yield self.position

        #skip unused positions
        for i in range(self.proxCount):

            self.proxStream.readVInt()            

        self.doc, self.frq = SegmentTermDocs.next(self)
        self.proxCount = self.frq
        self.position = 0
        return self.doc, self.frq, nextPosition(self.frq)


    def skippingDoc(self):
        # skip all positions
        for f in range(self.frq, 0, -1):
            self.proxStream.readVInt()    

    def seekTi(self, ti):
        SegmentTermDocs.seekTi(self, ti)

        if ti is not None:
            self.proxStream.seek(ti.proxPointer)
        else:
            self.proxCount = 0           
            
    def __repr__(self):
        s = '<stp>' + str(self.position)
        return s

class SegmentMergeInfo(object):

    def __init__(self, b, te, r):
        self.base = b
        self.reader = r
        self.termEnum = te
        self.term = te.term
        self.docMap = None
        self.postings = SegmentTermPositions(r)

        if self.reader.deletedDocs is not None:
            # build array with maps document numbers around deletions
            deletedDocs = self.reader.deletedDocs
            maxDoc = self.reader.maxDoc()
            self.docMap = [0] * maxDoc
            j = 0
            for i in range(maxDoc):
                if deletedDocs.get(i):
                    self.docMap[i] = -1
                else:
                    self.docMap[i] += 1
            

    def close(self):
        self.termEnum.close()
        self.postings.close()


    def advance(self):
        #I don't see a reasonable way out of this one.
        try:
            self.term, self.indexPointer= self.termEnum.next()
            self.trmInfo = self.termEnum.termInfo()
            return True
        except StopIteration: 
            self.term = None
            return False

    def __repr__(self):
        return '<SegMergInfo' + str(self.term) +'>'

    def __lt__(a, b):
        if a.term == b.term:
            return a.base < b.base
        else:
            return a.termEnum < b.termEnum 


    
class SegmentMerger(object):

    def __init__(self, dir, name):
        self.directory = dir
        self.segment = name
        self.freqOutput = None
        self.proxOutput = None
        self.termInfosWriter = None
        self.readers = []
        self.termInfo = term.TermInfo()
        self.smis = []
        
    def add(self, reader):
        self.readers.append(reader)

        
    def appendPostings(self, smis, n):
        lastDoc = 0
        df = 0          # number of with term

        for i in range(n):
            smi = smis[i]
            postings = smi.postings
            base = smi.base
            docMap = smi.docMap
            smi.termEnum.termInfo(self.termInfo)
            postings.seekTi(self.termInfo)

            for doc, freq, nextPos in postings:
                if docMap is None:
                    # no deletions
                    d = base + doc
                else:
                    # re-map around deletions
                    d = base + docMap[postings.doc]
                if d < lastDoc:
                    raise RuntimeException, 'docs out of order'

                # use low bit ot flag freq = 1
                docCode = (d - lastDoc) << 1
                lastDoc = d
    
                if freq == 1:
                    # write doc & freq=1
                    self.freqOutput.writeVInt(docCode | 1)
                else:
                    # write doc
                    self.freqOutput.writeVInt(docCode)
                    # write frequency in doc
                    self.freqOutput.writeVInt(freq)
    
                lastPosition = 0
                for position in nextPos:
                    self.proxOutput.writeVInt(position - lastPosition)
                    lastPosition = position
    
                df += 1

        return df


    def merge(self):
        try:
            self.mergeFields()
            self.mergeTerms()
            self.mergeNorms()
        finally:
            for reader in self.readers:
                reader.close()


    def mergeFields(self):
        # merge field names
        self.fieldInfos = field.FieldInfos()
        for reader in self.readers:
            self.fieldInfos.addFieldInfos(reader.fieldInfos)
        self.fieldInfos.writeDir(self.directory, self.segment + '.fnm')

        # merge field values
        fieldsWriter = field.FieldsWriter(self.directory,
                                                 self.segment,
                                                 self.fieldInfos)

        try:
            for reader in self.readers:
                deletedDocs = reader.deletedDocs
                maxDoc = reader.maxDoc()
                for j in range(maxDoc):
                    if deletedDocs is None or not deletedDocs.get(j):
                        # skip deleted docs
                        fieldsWriter.addDocument(reader.document(j))
        finally:
            fieldsWriter.close()
                                                 
        

    def mergeNorms(self):
        for i in range(len(self.fieldInfos)):
            fi = self.fieldInfos.fieldInfoInt(i)
            if fi.isIndexed:
                output = self.directory.createFile(self.segment + '.f' + str(i))
                try:
                    for reader in self.readers:
                        deletedDocs = reader.deletedDocs
                        input = reader.normStream(fi.name)
                        maxDoc = reader.maxDoc()
                        try:
                            for k in range(maxDoc):
                                if input is None:
                                    norm = 0
                                else:
                                    norm = input.readByte()
                                output.writeByte(norm)
                        finally:
                            if input is not None:
                                input.close()
                finally:
                    output.close()


    def mergeTermInfo(self, smis, n):
        freqPointer = self.freqOutput.getFilePointer()
        proxPointer = self.proxOutput.getFilePointer()

        # Append posting data
        df = self.appendPostings(smis, n)

        if df > 0:
            # add an entry to the dictionary with pointers to prox and freq files
            self.termInfo.set(df, freqPointer, proxPointer)
            self.termInfosWriter.add(smis[0].term, self.termInfo)



    def mergeTermInfos(self):
        smis = self.smis 
        base = 0


        for reader in self.readers:
            termEnum = reader.terms()
            smi = SegmentMergeInfo(base, termEnum, reader)
            base += reader.numDocs()
            if smi.advance():
                insort(smis, smi)
            else:
                smi.close()

        match = [0] * len(self.readers)
        while len(smis) > 0:
            # pop matching terms
            matchSize = 0
            match[matchSize] = smis.pop(0)
            matchSize += 1
            term = match[0].term
            top =  smis and smis[0] or None
            
            while top is not None and cmp(term,top.term) == 0:
                match[matchSize] = smis.pop(0)
                matchSize += 1
                top =  smis and smis[0] or None
                    
            # add new TermInfo
            self.mergeTermInfo(match, matchSize)
            
            while matchSize > 0:
                matchSize -= 1
                smi = match[matchSize]
                if smi.advance():
                    insort(smis, smi)
                else:
                    smi.close()


    def mergeTerms(self):
        try:
            self.freqOutput = self.directory.createFile(self.segment + '.frq')
            self.proxOutput = self.directory.createFile(self.segment + '.prx')
            self.termInfosWriter = term.TermInfosWriter(self.directory,
                                                                  self.segment,
                                                                  self.fieldInfos)
            self.mergeTermInfos()
        finally:
            if self.freqOutput is not None:
                self.freqOutput.close()
            if self.proxOutput is not None:
                self.proxOutput.close()
            if self.termInfosWriter is not None:
                self.termInfosWriter.close()
            for smi in self.smis:
                smi.close()
    
    def segmentReader(self, i):
        return self.readers[i]

    
class SegmentReader(IndexReader):
    
    # Class methods
    def hasDeletions(cls, si):
        return si.dir.fileExists(si.name + '.del')
    
    hasDeletions = classmethod(hasDeletions)
    

    # instance methods
    def __init__(self, si, closeDir=False):
        self.directory = si.dir
        self.closeDirectory = closeDir
        self.segment = si.name
        self.nrms = {}
        self.deletedDocsDirty = False

        self.fieldInfos = field.FieldInfos(self.directory,
                                                self.segment + '.fnm')
        self.fieldsReader = field.FieldsReader(self.directory,
                                                      self.segment,
                                                      self.fieldInfos)

        self.tis = TermInfosReader(self.directory,
                                                   self.segment,
                                                   self.fieldInfos)

        if SegmentReader.hasDeletions(si):
            self.deletedDocs = BitVector(self.directory,
                                                   self.segment + '.del')
        else:
            self.deletedDocs = None

        # makes sure that all index files have been read or are kept open
        # so that if an index update removes them we'll still have them
        self.freqStream = self.directory.openFile(self.segment + '.frq')
        self.proxStream = self.directory.openFile(self.segment + '.prx')

        self.openNorms()


    def closeNorms(self):
        for v in self.nrms.values():
            norm = v
            v.inStream.close()


    def docFreq(self, t):
        ti = self.tis.getTerm(t)
        if ti is None:
            return 0
        else:
            return ti.docFreq


    def doClose(self):
        if self.deletedDocsDirty:
            self.deletedDocs.write(self.directory, self.segment + ".tmp")
            self.directory.renameFile(self.segment + ".tmp",
                                      self.segment + ".del")
            self.deletedDocsDirty = False

        self.fieldsReader.close()
        self.tis.close()

        if self.freqStream is not None:
            self.freqStream.close()
        if self.proxStream is not None:
            self.proxStream.close()

        self.closeNorms()

        if self.closeDirectory:
            self.directory.close()


    def document(self, n):
        if self.isDeleted(n):
            raise Exception, 'attempt to access deleted document'
        return self.fieldsReader.doc(n)


    def doDelete(self, docNum):
        if self.deletedDocs is None:
            self.deletedDocs = BitVector(self.maxDoc())
        self.deletedDocsDirty = True
        self.deletedDocs.set(docNum)


    def files(self):
        suffix = ['.fnm','.fdx','.fdt','.tii','.tis','.frq','.prx']
        files = map((lambda x: self.segment + x), suffix)

        if self.directory.fileExists(self.segment + '.del'):
            files.append(self.segment + '.del')
            
        for i in range(len(self.fieldInfos)):
            fi = self.fieldInfos.fieldInfoInt(i)
            if fi.isIndexed:
                files.append(self.segment + '.f' + str(i))
                
        return files


    def isDeleted(self, n):
        return (self.deletedDocs is not None and self.deletedDocs.get(n))


    def maxDoc(self):
        return self.fieldsReader.size()
    

    def normsField(self, field):
        norm = self.nrms.get(field, None)
        if norm is None:
            return None
        if norm.bytes is None:
            bytes = array('B',[0x00]*self.maxDoc())
            self.norms(field, bytes, 0)
            norm.bytes = bytes

        return norm.bytes
    

    def norms(self, field, bytes, offset):
        normStream = self.normStream(field)
        if normStream is None:
            return
        try:
            normStream.readBytes(bytes, offset, self.maxDoc())
        finally:
            normStream.close()


    def normStream(self, field):
        norm = self.nrms.get(field, None)
        if norm is None:
            return None
        # Cloning????
        result = norm.inStream.clone()
        result.seek(0)
        return result


    def numDocs(self):
        n = self.maxDoc()
        if self.deletedDocs is not None:
            n -= self.deletedDocs.count()
        return n

    def openNorms(self):
        for i in range(len(self.fieldInfos)):
            fi = self.fieldInfos.fieldInfoInt(i)
            if fi.isIndexed:
                self.nrms[fi.name]=Norm(self.directory.openFile(
                    (self.segment + '.f' + str(fi.number))))
                

    def termDocs(self):
        return SegmentTermDocs(self)
        


    def termPositions(self):
        return SegmentTermPositions(self)
    

    def terms(self, t = None):
        return self.tis.terms(t)

    def fieldNames(self):
        # Experimental for auto-queries
        # Return a sorted list of all the field names
        fNames = self.fieldInfos.fieldNames()
        if not fNames:
            return []
        # Remove the field with no name
        fNames.remove('')
        return fNames
        


class Norm(object):

    def __init__(self, inStream):
        self.inStream = inStream
        self.bytes = None

            
class SegmentsReader(IndexReader):

    def __init__(self, directory, r):
        IndexReader.__init__(self, directory)
        self.readers = r
        self.maxiDoc = 0
        self.normsCache = {}
        self.numiDocs = -1
        self.starts = [0]
        
        i = 0
        for reader in self.readers:
            self.maxiDoc += reader.maxDoc()
            self.starts.append(self.maxiDoc)

    def docFreq(self, t):
        total = 0
        for r in self.readers:
            total += r.docFreq(t)
        return total


    def doClose(self):
        for r in self.readers:
            r.close()


    def document(self, n):
        # find segment num
        i = self.readerIndex(n)
        # dispatch to segment reader
        return self.readers[i].document(n - self.starts[i])    


    def doDelete(self, n):
        # invalidate cache
        self.numiDocs = -1
        # find seg num
        i = self.readerIndex(n)
        # dispatch to seg reader
        self.readers[i].doDelete(n - self.starts[i])


    def isDeleted(self, n):
        # find segment num
        i = self.readerIndex(n)
        # dispatch to segment reader
        return self.readers[i].isDeleted(n - self.starts[i])


    def maxDoc(self):
        return self.maxiDoc


    def normsField(self, field):
        bytes = self.normsCache.get(field, None)
        if bytes is not None:
            # cache hit
            return bytes

        bytes = array('B',[0x00] * self.maxDoc())
        for i in range(len(self.readers)):
            self.readers[i].norms(field, bytes, self.starts[i])
        # update cache
        self.normsCache[field]=bytes
        return bytes


    #def numDocs(self):
    #    # check cache
    #    if numiDocs == -1:
    #        # cache miss - recompute
    #        n = 0
    #        for r in self.readers:
    #            # sum from readers
    #            n += r.numDocs()
    #        self.numiDocs = n
    #    return self.numiDocs


    def readerIndex(self, n):
        # Search starts array for first element less than n
        lo = 0
        hi = len(self.readers) - 1

        while hi >= lo:
            mid = (lo + hi) >> 1
            midValue = self.starts[mid]
            if n < midValue:
                hi = mid - 1
            elif n > midValue:
                lo = mid + 1
            else:
                return mid
        return hi


    def termDocs(self):
        return SegmentsTermDocs(self.readers, self.starts)


    def termPositions(self):
        return SegmentsTermPositions(self.readers, self.starts)

    def terms(self, t = None):
        return SegmentsTermEnum(self, t)
    
    def fieldNames(self):
        # Experimental for auto-queries
        if self.readers:
            return self.readers[0].fieldInfos.fieldNames()
        else:
            return []

class SegmentsTermEnum(segment.SegmentTermEnum):

    def __init__(self, segmentsreader, term=None):
        self.enums = [sr.terms(term) for sr in segmentsreader.readers]
        self.prev = None
        min = self.enums[0]
        for enum in self.enums:
            if enum.term is not None and enum < min:
                min = enum
        self.term = min.term

    def close(self):
        for e in self.enums: e.close()

    def next(self):
        min = self.enums[0]
        for enum in self.enums:
            if enum.term is not None and enum<min:
                min = enum
        if min.term is None:
            raise StopIteration
        else:
            self.prev = self.term
            self.term = min.term
            try:
                min.next()
            except StopIteration:
                pass


class SegmentsTermDocs(object):

    def __init__(self, r, s):
        self.readers = r
        self.starts = s

        self.base = 0
        self.pointer = 0
        self.current = None
        self.term = None
        
        self.segTermDocs = [None] * len(r)


    def close(self):
        for segtdoc in self.segTermDocs:
            if segtdoc is not None:
                segtdoc.close()

    def freq(self):
        return self.current.frq
    frq = property(freq) # what can i say? API in transition

    def __iter__(self):
        def x():
            if self.current is not None:
                for item in self.current:
                    yield item
            for ptr, reader in list(enumerate(self.readers))[self.pointer:]:
                self.pointer = ptr
                self.base = self.starts[self.pointer]
                self.current = self.termDocsInt(self.pointer)
                for item in self.current:
                    yield (item[0]+self.base,) + item[1:]
        return x()


    def read(self):
        dfs = []
        while True:
            while self.current is None:
                if self.pointer < len(self.readers):
                    # try next segment
                    self.base = self.starts[self.pointer]
                    self.current = self.termDocsInt(self.pointer)
                    self.pointer += 1
                else:
                    return dfs
            segmentDFs = self.current.read()
            if segmentDFs:
                b = self.base
                for i, (d, f) in enumerate(segmentDFs):
                    segmentDFs[i] = d + b, f
                dfs.extend(segmentDFs)
            else:
                self.current = None


    def seekTerm(self, term):
        self.term = term
        self.base = 0
        self.pointer = 0
        self.current = None

    def termDocsInt(self, i):
        if self.term is None:
            return None
        result = self.segTermDocs[i]
        if result is None:
            result = self.termDocsReader(self.readers[i])
            self.segTermDocs[i] = result
        result.seekTerm(self.term)
        return result


    def termDocsReader(self, reader):
        return reader.termDocs()



class SegmentsTermPositions(SegmentsTermDocs):
        
    def termDocsReader(self, reader):
        return reader.termPositions()


    #def nextPosition(self):
    #    return self.current.nextPosition()

class TermInfosReader(object):

    def __init__(self, d, seg, fis):
        self.directory = d
        self.segment = seg
        self.fieldInfos = fis
        
        self.indexTerms = None

        self.enum = segment.SegmentTermEnum(
            self.directory.openFile(self.segment + '.tis'),
            self.fieldInfos,
            False)
        
        self.sze = self.enum.size
        self.readIndex()


    def close(self):
        if self.enum is not None:
            self.enum.close()



    def getInt(self, position):
        if self.sze == 0:
            return None

        if (self.enum is not None and self.enum.term() is not None and
            position > self.enum.position and
            position < (self.enum.position + term.TermInfosWriter.INDEX_INTERVAL)):
            # can avoid seek
            return self.scanEnum(position)

        # must seek
        self.seekEnum(position/term.TermInfosWriter.INDEX_INTERVAL)
        return self.scanEnum(position)


    def getIndexOffset(self, term):
        #TODO - use bisect module?
  
        lo = 0
        hi = len(self.indexTerms) - 1
        
        while hi >= lo:
            mid = (lo + hi) >> 1
            delta = cmp(term, self.indexTerms[mid])
            if delta < 0:
                hi = mid - 1
            elif delta > 0:
                lo = mid + 1
            else:
                return mid
                
        return hi
    

    def getTerm(self, t):
        if self.sze == 0:
            return None

        # Optimize sequential access: first try scanning
        # cached enum w/o seeking

        if (self.enum.term is not None and
            ((self.enum.prev is not None and cmp(t,self.enum.prev) > 0) or
             cmp(t,self.enum.term) >= 0)):
            # term is at or past current
            enumOffset = (self.enum.position/term.TermInfosWriter.INDEX_INTERVAL)+1

            if (len(self.indexTerms) == enumOffset or
                cmp(t, self.indexTerms[enumOffset]) < 0):
                # but before end of block
                # no need to seek
                return self.scanEnum(t)

        # random-access: must seek
        self.seekEnum(self.getIndexOffset(t))
        return self.scanEnum(t)
                                          


    def getPosition(self, term):
        if size == 0:
            return -1

        indexOffset = self.getIndexOffest(term)
        self.seekEnum(indexOffset)

        while (term > self.enum.term()) and self.enum.advance():
            pass

        if term == self.enum.term():
            return self.enum.position
        else:
            return -1


    def readIndex(self):
        indexEnum = segment.SegmentTermEnum(
            self.directory.openFile(self.segment + '.tii'),
            self.fieldInfos,
            True)

        try:
            indexSize = indexEnum.size

            self.indexTerms = []
            self.indexInfos = []
            self.indexPointers = []

            for term, indexPointer in indexEnum:
                self.indexTerms.append(indexEnum.term)
                self.indexInfos.append(indexEnum.termInfo())
                self.indexPointers.append(indexEnum.indexPointer)

        finally:
            indexEnum.close()


    def scanEnum(self, position):
        while(self.enum.position < position):
            if not enum.next():
                return None
        return self.enum.term()


    def scanEnum(self, term):
        # Scans within block for matching term.
        t = self.enum.term
        while (cmp(term, t) > 0):
            try:
                #ugh ugh it is 7am make it stop
                t = self.enum.next()[0]
            except StopIteration:
                break
        if (self.enum.term is not None and cmp(term, self.enum.term) == 0):
            return self.enum.termInfo()
        else:
            return None


    def seekEnum(self, indexOffset):
        self.enum.seek(self.indexPointers[indexOffset],
                       (indexOffset * term.TermInfosWriter.INDEX_INTERVAL) - 1,
                       self.indexTerms[indexOffset], self.indexInfos[indexOffset])

    def terms(self, term = None):
        if term is None:
            # Returns an enumeration of all the Terms and TermInfos in the set
            if (self.enum.position != -1):
                # if not at start
                # reset to start
                self.seekEnum(0)
        else:
            self.getTerm(term)
            
        res = self.enum.clone()
        return res
    
