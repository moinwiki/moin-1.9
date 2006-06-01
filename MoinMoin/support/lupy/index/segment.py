# -*- test-case-name: lupy.test -*- 
# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

from MoinMoin.support.lupy.index import term

#import copy #broken, see comments at top of this file:
from MoinMoin.support import copy

class SegmentTermEnum:

    def __init__(self, i, fis, isi):
        self.input = i
        self.fieldInfos = fis
        self.size = self.input.readInt()
        self.isIndex = isi

        self.indexPointer = 0
        self.position = -1
        self.prev = None
        self.prevTxt = ''
        self.term = term.Term('','')
        self.trmInfo = term.TermInfo()
    
    
    def clone(self):
        """Return a copy of self.
        """
        
        # TODO: implement as __copy__
        clone = copy.copy(self)
        clone.input = self.input.clone()
       
        clone.trmInfo = term.TermInfo()
        clone.trmInfo.setTo(self.trmInfo)
        #clone.prevTxt = self.term.text()
        return clone


    def close(self):
        self.input.close()


    def docFreq(self):
        return self.trmInfo.docFreq


    def freqPointer(self):
        return self.trmInfo.freqPointer


    def next(self):
        self.position += 1
        
        if self.position > self.size -1:
            self.position += 1
            self.term = None
            raise StopIteration

        self.prev = self.term
        self.term = self.readTerm()

        self.trmInfo.docFreq = self.input.readVInt()
        self.trmInfo.freqPointer += self.input.readVLong()
        self.trmInfo.proxPointer += self.input.readVLong()

        if self.isIndex:
            self.indexPointer += self.input.readVLong()
            
        return self.term, self.indexPointer

    def __iter__(self):
        return self

    def proxPointer(self):
        return self.trmInfo.proxPointer


    def readTerm(self):
        # this bit is a mite tricky. in the java version they use a
        # buffer for reading and just use 'start' as the offset for
        # putting the read string into the buffer; when strings with
        # common prefixes were read in, the offset would preserve the
        # prefix. So here we just remember the last string and slice
        # the common prefix from it.        
        start = self.input.readVInt()        
        self.prevTxt = txt = self.prevTxt[:start] + self.input.readString()        
        fi = self.input.readVInt()
        fld = self.fieldInfos.fieldName(fi)        
        t = term.Term(fld,txt,False)
        return t


    def seek(self, pointer, p, t, ti):
        self.input.seek(pointer)
        self.position = p
        self.term = t
        self.prev = None
        self.trmInfo.setTo(ti)
        self.prevTxt = self.term.text()

    def termInfo(self, ti=None):
        if ti is None:
            nti = term.TermInfo()
            nti.setTo(self.trmInfo)
            return nti
        else:
            ti.setTo(self.trmInfo)

    def __cmp__(a, b):
        return cmp(a.term, b.term)


class SegmentInfo(object):

    def __init__(self, name, docCount, d):
        self.name = name
        self.docCount = docCount
        self.dir = d


class SegmentInfos(list):

    def __init__(self, lst = None):
        self.counter = 0
        if lst is not None:
            self.extend(lst)
    
    def __getslice__(self, lo, hi):
        res = SegmentInfos(list.__getslice__(self, lo, hi))
        res.counter = self.counter
        return res
    
    def read(self, directory):
        input = directory.openFile('segments')
        try:
            self.counter = input.readInt()      # read counter
            i = input.readInt()
            while i > 0:                        # read segment infos
                si = SegmentInfo(input.readString(),
                                             input.readInt(),
                                             directory)
                self.append(si)
                i -= 1
        finally:
            input.close()

    def write(self, directory):
        output = directory.createFile('segments.new')
        try:
            output.writeInt(self.counter)
            output.writeInt(len(self))
            for si in self:
                output.writeString(si.name)
                output.writeInt(si.docCount)
        finally:
            output.close()

        # Install new segment info
        directory.renameFile('segments.new','segments')
        
    def __repr__(self):
        return 'SegInfo' + list.__repr__(self)
        

