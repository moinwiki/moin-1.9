# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

class Term(object):
    
    def __init__(self, fld, txt, intern=False):
        self.set(fld, txt)

    def __cmp__(self, other):
        """Compares two terms, returning an integer which is less than zero iff this
        term belongs after the argument, equal zero iff this term is equal to the
        argument, and greater than zero iff this term belongs after the argument.

        The ordering of terms is first by field, then by text."""

        if self.fld == other.fld:
            # fields are interned
            return cmp(self.txt, other.txt)
        else:
            return cmp(self.fld, other.fld)

    def __hash__(self):
        return self._hash
    
    def field(self):
        return self.fld
    
    def readObject(self, inp):
        inp.defaultReadObject()

    def set(self, fld, txt):
        self.fld = fld
        self.txt = txt
        self._hash = hash(fld + txt)

    def text(self):
        return self.txt

    def __repr__(self):
        return 'Term<'+self.fld.encode('utf8')+':'+self.txt.encode('utf8')+'>'

class TermInfo(object):

    def __init__(self):
        self.docFreq = 0
        self.freqPointer = 0
        self.proxPointer = 0

    def set(self, df, fp, pp):
        self.docFreq = df
        self.freqPointer = fp
        self.proxPointer = pp

    def setTo(self, ti):
        self.docFreq = ti.docFreq
        self.freqPointer = ti.freqPointer
        self.proxPointer = ti.proxPointer

    def __repr__(self):
        return '<TermInfo:d:' + str(self.docFreq)+ ' f:' + str(self.freqPointer) +\
               ' p:' + str(self.proxPointer) + '>'


class TermInfosWriter(object):
    INDEX_INTERVAL = 128


    def __init__(self, d, seg, fis, isIndex = False):
        
        self.initialize(d, seg, fis, isIndex)
        
        self.size = 0
        self.lastIndexPointer = 0
        self.lastTerm = Term('','')
        self.lastTi = TermInfo()
        
        if isIndex is False:
            self.other = TermInfosWriter(d, seg, fis, True)
            self.other.other = self

            
    def initialize(self, d, seg, fis, isi):
        self.fieldInfos = fis
        self.isIndex = isi
        if isi is True:
            ext = '.tii'
        else:
            ext = '.tis'
            
        self.output=d.createFile(seg + ext)
        # leave space for size
        self.output.writeInt(0)


    def stringDifference(self, s1, s2):
        prefixLength = min(len(s1), len(s2))
        for i in range(prefixLength):
            if s1[i] != s2[i]:
                return i
        
        return prefixLength


    def add(self, term, ti):
        if not self.isIndex and term <= self.lastTerm:
            raise Exception, "term out of order: " + str(term) + str(self.lastTerm)
        if ti.freqPointer < self.lastTi.freqPointer:
            raise Exception, "freqPointer out of order"
        if ti.proxPointer < self.lastTi.proxPointer:
            raise Exception, "proxPointer out of order"

        if (not self.isIndex and self.size % self.INDEX_INTERVAL == 0):
            # add an index term
            self.other.add(self.lastTerm, self.lastTi)

        # write term
        self.writeTerm(term)
        # write doc freq
        self.output.writeVInt(ti.docFreq)
        # write pointers
        self.output.writeVLong(ti.freqPointer - self.lastTi.freqPointer)
        self.output.writeVLong(ti.proxPointer - self.lastTi.proxPointer)

        if self.isIndex:
            self.output.writeVLong(self.other.output.getFilePointer() - self.lastIndexPointer)
            self.lastIndexPointer = self.other.output.getFilePointer()

        self.lastTi.setTo(ti)
        self.size += 1


    def close(self):
        self.output.seek(0)
        self.output.writeInt(self.size)
        self.output.close()

        if self.isIndex is not True:
            self.other.close()


    def writeTerm(self, term):
        a, b = self.lastTerm.text(), term.text()
        start = self.stringDifference(a, b)
        delta = term.text()[start:]
        # write shared prefix length
        self.output.writeVInt(start)
        # write delta chars
        self.output.writeString(delta)
        # write field num
        i = self.fieldInfos.fieldNumber(term.field())
        self.output.writeVInt(i)
        self.lastTerm = term



