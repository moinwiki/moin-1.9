# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

from StringIO import StringIO
from array import array
import re
from MoinMoin.support.lupy.search import similarity
from MoinMoin.support.lupy.index import field, term

def standardTokenizer(string):
    """Yield a stream of downcased words from a string."""
    r = re.compile("\\w+", re.U)
    tokenstream = re.finditer(r, string)
    for m in tokenstream:
        yield m.group().lower()
        
class DocumentWriter(object):

    def __init__(self, directory, analyzer=None, mfl=None):
        self.directory = directory
        self.maxFieldLength = mfl
        self.postingTable = {}
        self.termBuffer = term.Term('','')
        self.analyzer=analyzer or standardTokenizer
        
    def addDocument(self, segment, doc):
        # Write field names
        fi = self.fieldInfos = field.FieldInfos()
        fi.add(doc)
        fi.writeDir(self.directory, segment + '.fnm')

        # Write field values
        fieldsWriter = field.FieldsWriter(self.directory,
                                                 segment,
                                                 self.fieldInfos)
        try:
            fieldsWriter.addDocument(doc)
        finally:
            fieldsWriter.close()

        # Invert doc into postingTable
        self.postingTable = {}
        self.fieldLengths = [0] * (len(self.fieldInfos))
        self.invertDocument(doc)

        # Sort postingTable into an array
        postings = self.sortPostingTable()


        # Write postings
        self.writePostings(postings, segment)
        
        # Write noms of indexed files
        self.writeNorms(doc, segment)


    def invertDocument(self, doc):
        fields = doc.fields()
        for field in doc.fields():
            fieldName = field.name()
            fieldNumber = self.fieldInfos.fieldNumber(fieldName)
            
            position = self.fieldLengths[fieldNumber]    # Position in field

            if field.isIndexed:
                if not field.isTokenized:
                    # Untokenized
                    self.addPosition(fieldName, field.stringValue(), position)
                    position += 1
                else:
                    # Find or make a reader
                    if field.readerValue() is not None:
                        val = field.readerValue().read()
                    elif field.stringValue() is not None:
                        val = field.stringValue()
                    else:
                        raise Exception, 'Field must have either a String or Reader value'
                    
                    for tok in self.analyzer(val):
                        self.addPosition(fieldName, tok, position)
                        position += 1

                        if self.maxFieldLength and (position > self.maxFieldLength):
                            break
                        
            self.fieldLengths[fieldNumber] = position 
                    

    def addPosition(self, field, text, position):
        self.termBuffer.set(field, text)

        ti = self.postingTable.get(self.termBuffer, None)
        
        if ti is not None:
            freq = ti.freq
            ti.positions.append(position)
            ti.freq = freq + 1
        else:
            trm = term.Term(field, text, False)
            self.postingTable[trm] = Posting(trm, position)


    def sortPostingTable(self):
        arr = self.postingTable.values()
        arr.sort()
        return arr


    def writePostings(self, postings, segment):
        freq = None
        prox = None
        tis = None

        try:
            freq = self.directory.createFile(segment + '.frq')
            prox = self.directory.createFile(segment + '.prx')

            tis = term.TermInfosWriter(self.directory,
                                                  segment,
                                                  self.fieldInfos)
            ti = term.TermInfo()

            for posting in postings:
                # print 'writing', posting, posting.term
                # Add entry to the dictionary with pointers to prox and freq files
                ti.set(1, freq.getFilePointer(), prox.getFilePointer())
                tis.add(posting.term, ti)

                # Add an entry to the freq file
                f = posting.freq
                if f == 1:                  # optimize freq == 1
                    freq.writeVInt(1)       # set low bit of doc num
                else:
                    freq.writeVInt(0)       # the document number
                    freq.writeVInt(f)       # frequency in doc

                lastPosition = 0
                positions = posting.positions

                for position in positions:
                    prox.writeVInt(position - lastPosition)
                    lastPosition = position
                    
        finally:
            if freq is not None:
                freq.close()
            if prox is not None:
                prox.close()
            if tis is not None:
                tis.close()


    def writeNorms(self, doc, segment):
        for field in doc.fields():
            if field.isIndexed:
                fieldNumber = self.fieldInfos.fieldNumber(field.name())
                norm = self.directory.createFile(segment +
                                                 '.f' + str(fieldNumber))
                try:
                    norm.writeByte(similarity.normInt(self.fieldLengths[fieldNumber]))
                finally:
                    norm.close()


class Posting(object):

    def __init__(self, t, position):
        self.term = t
        self.freq = 1
        self.positions = array('i',[1])
        self.positions[0] = position

    def __repr__(self):
        s = '<Posting:'
        s += str(self.term) + '>'
        return s

    def __cmp__(self, other):
        return cmp(self.term, other.term)
