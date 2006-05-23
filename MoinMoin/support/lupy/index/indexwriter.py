# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

import sys

from MoinMoin.support.lupy import store
from MoinMoin.support.lupy.index import segmentmerger, segment, documentwriter

class IndexWriter(object):

    def __init__(self, path, create=False, analyzer=None):
        if path is None:
            if create is True:
                self.directory = store.RAMDirectory()
            else:
                self.directory = path
        else:
            self.directory = store.FSDirectory(path, create)
            
        self.infoStream = None
        self.analyzer = analyzer
        self.maxMergeDocs = sys.maxint
        self.mergeFactor = 20 # Never < 2
        self.segmentInfos = segment.SegmentInfos()
        self.ramDirectory = store.RAMDirectory()
        # self.writeLock = open("write.lock", "wb")
        # locker.lock(self.writeLock, locker.LOCK_EX)
        
        if create is True:
            self.segmentInfos.write(self.directory)
        else:
            self.segmentInfos.read(self.directory)


    def close(self):
        self.flushRamSegments()
        self.ramDirectory.close()
        # self.writeLock.close()
        self.directory.close()


    def docCount(self):
        count = 0
        for si in self.segmentInfos:
            count += si.docCount
        return count


    def addDocument(self, doc):
        dw = documentwriter.DocumentWriter(self.ramDirectory, self.analyzer)
        segmentName = self.newSegmentName()
        dw.addDocument(segmentName, doc)
        self.segmentInfos.append(segment.SegmentInfo(segmentName, 1, self.ramDirectory))
        self.maybeMergeSegments()


    def newSegmentName(self):
        res = '_' + str(self.segmentInfos.counter)
        self.segmentInfos.counter += 1
        return res


    def optimize(self):
        self.flushRamSegments()
        while ((len(self.segmentInfos) > 1) or (len(self.segmentInfos) == 1 and
                (segmentmerger.SegmentReader.hasDeletions(self.segmentInfos[0]) or
                 self.segmentInfos[0].dir != self.directory))):
            minSegment = (len(self.segmentInfos) - self.mergeFactor)
            if minSegment < 0:
                self.mergeSegments(0)
            else:
                self.mergeSegments(minSegment)


    def addIndexes(self, dirs):
        """Merges all segments from an array of indexes into this index.
        
        This may be used to parallelize batch indexing.  A large document
        collection can be broken into sub-collections.  Each sub-collection can be
        indexed in parallel, on a different thread, process or machine.  The
        complete index can then be created by merging sub-collection indexes
        with this method.
        
        After this completes, the index is optimized."""
        #### UNTESTED ####
        self.optimize()
        for d in dirs:
            sis = segment.SegmentInfos()
            sis.read(d)
            for j in range(len(sis)):
                self.segmentInfos.append(sis[j])
        self.optimize()


    def flushRamSegments(self):
        """Merges all RAM-resident segments."""
        
        sis = self.segmentInfos
        minSegment = len(sis) - 1
        docCount = 0

        while minSegment >= 0 and ((sis[minSegment]).dir == self.ramDirectory):
            docCount += sis[minSegment].docCount
            minSegment -= 1

        if (minSegment < 0 or (docCount + sis[minSegment].docCount) > self.mergeFactor or
            not (sis[len(sis)-1].dir == self.ramDirectory)):
            minSegment += 1

        if minSegment >= len(sis):
            return
        self.mergeSegments(minSegment)


    def maybeMergeSegments(self):
        """Incremental segment merger"""
        
        targetMergeDocs = self.mergeFactor
        while targetMergeDocs <= self.maxMergeDocs:
            # Find segment smaller than the current target size
            minSegment = len(self.segmentInfos)
            mergeDocs = 0
            minSegment -= 1
            while minSegment >= 0:
                si = self.segmentInfos[minSegment]
                if si.docCount >= targetMergeDocs:
                    break
                mergeDocs += si.docCount
                minSegment -= 1
            if mergeDocs >= targetMergeDocs:    #found a merge to do
                self.mergeSegments(minSegment + 1)
            else:
                break
            targetMergeDocs *= self.mergeFactor       # increase target size
            

    def mergeSegments(self, minSegment):
        """Pops segments off of segmentInfos stack down to minSegment,
        merges them, and pushes the merged index onto the top of the
        segmentInfos stack"""
        
        mergedName = self.newSegmentName()
        mergedDocCount = 0
        merger = segmentmerger.SegmentMerger(self.directory, mergedName)
        segmentsToDelete = []

        for i in range(minSegment, len(self.segmentInfos)):
            si = self.segmentInfos[i]
            reader = segmentmerger.SegmentReader(si)
            merger.add(reader)
            if reader.directory is self.directory or reader.directory is self.ramDirectory:
                segmentsToDelete.append(reader)
            mergedDocCount += si.docCount
        merger.merge()

        self.segmentInfos = self.segmentInfos[:minSegment]
        self.segmentInfos.append(segment.SegmentInfo(mergedName,
                                                         mergedDocCount,
                                                         self.directory))

        # TODO some locking here
        self.segmentInfos.write(self.directory)     # commit before deleting
        self.deleteSegments(segmentsToDelete)      # delete now-unused segments
        

    def deleteSegments(self, segs):
        """Some operating systems (e.g. Windows) don't permit a file to be deleted
        while it is opened for read (e.g. by another process or thread).  So we
        assume that when a delete fails it is because the file is open in another
        process, and queue the file for subsequent deletion."""
        
        deletable = []

        self.deleteFilesList(self.readDeleteableFiles(), deletable) # try to delete deletable

        for reader in segs:
            if reader.directory is self.directory:
                self.deleteFilesList(reader.files(), deletable)     # try to delete our files
            else:
                self.deleteFilesDir(reader.files(), reader.directory)  # delete, eg, RAM files
            self.writeDeleteableFiles(deletable)                # note files we can't delete
            

    def deleteFilesDir(self, files, dir):
        for file in files:
            dir.deleteFile(file)


    def deleteFilesList(self, files, deletable):
        for file in files:
            try:
                self.directory.deleteFile(file)
            except OSError:
	        # this occurs on windows where sometimes
		# win reports a file to be in use
		# in reality it is windows that is fiddling
		# with the file and locking it temporarily
                if self.directory.fileExists(file):
		    # schedule the file for later deletion
                    deletable.append(file)


    def readDeleteableFiles(self):
        result = []
        if not self.directory.fileExists('deletable'):
            return result
        input = self.directory.openFile('deletable')
        try:
            i = input.readInt()
            while i > 0:
                result.append(input.readString())
                i -= 1
        finally:
            input.close()
        return result


    def writeDeleteableFiles(self, files):
        output = self.directory.createFile('deletable.new')
        try:
            output.writeInt(len(files))
            for file in files:
                output.writeString(file)
        finally:
            output.close()
        self.directory.renameFile('deletable.new','deletable')
