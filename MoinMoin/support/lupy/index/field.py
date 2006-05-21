# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

from MoinMoin.support.lupy import document

class FieldInfo(object):

    def __init__(self, na, tk, nu):
        self.name = na
        self.isIndexed = tk
        self.number = nu


class FieldInfos(object):
        
    def __init__(self, d=None, name=None):
        self.byNumber = []
        self.byName = {}
        if d is None and name is None:
            self.addString('',False)
        else:
            input = d.openFile(name)
            try:
                self.read(input)
            finally:
                input.close()

    def add(self, doc):
        """Adds field info for a Document"""
        for field in doc.fields():
            self.addString(field.name(), field.isIndexed)

    def addString(self, name, isIndxd):
        fi = self.fieldInfo(name)
        if fi is None:
            self.addInternal(name, isIndxd)
        elif fi.isIndexed is not isIndxd:
            fi.isIndexed = True

    def addFieldInfos(self, other):
        """Merges in information from another FieldInfos"""
        for i in range(len(other)):
            fi = other.fieldInfoInt(i)
            self.addString(fi.name, fi.isIndexed)

    def addInternal(self, name, isIndexed):
        fi = FieldInfo(name, isIndexed, len(self.byNumber))

        self.byNumber.append(fi)
        self.byName[name]=fi

    def fieldNumber(self, fieldName):
        fi = self.fieldInfo(fieldName)
        if fi is not None:
            return fi.number
        else:
            return -1

    def fieldInfo(self, fieldName):
        return self.byName.get(fieldName, None)

    def fieldName(self, fieldNumber):
        return self.byNumber[fieldNumber].name

    def fieldInfoInt(self, fieldNumber):
        return self.byNumber[fieldNumber]

    def __len__(self):
        return len(self.byNumber)

    def writeDir(self, d, name):
        output = d.createFile(name)
        try:
            self.write(output)
        finally:
            output.close()

    def write(self, output):
        output.writeVInt(len(self))

        for i in range(len(self)):
            fi = self.fieldInfoInt(i)
            output.writeString(fi.name)
            if fi.isIndexed:
                output.writeByte(1)
            else:
                output.writeByte(0)

    def read(self, input):
        size = input.readVInt()
        for i in range(size):
            self.addInternal(input.readString(), (input.readByte() != 0))

    def fieldNames(self):
        # Experimental for auto-queries
        return self.byName.keys()

class FieldsWriter(object):

    def __init__(self, d, segment, fn):
        self.fieldInfos = fn
        self.fieldsStream = d.createFile(segment + '.fdt')
        self.indexStream = d.createFile(segment + '.fdx')


    def addDocument(self, doc):
        self.indexStream.writeLong(self.fieldsStream.getFilePointer())
        storedCount = 0
        for field in doc.fields():
            if field.isStored:
                storedCount += 1

        self.fieldsStream.writeVInt(storedCount)

        for field in doc.fields():
            if field.isStored:
                self.fieldsStream.writeVInt(self.fieldInfos.fieldNumber(field.name()))
    
                bits = 0
                if field.isTokenized:
                    bits |= 1
                self.fieldsStream.writeByte(bits)
    
                self.fieldsStream.writeString(field.stringValue())


    def close(self):
        self.fieldsStream.close()
        self.indexStream.close()

                                           
class FieldsReader(object):

    def __init__(self, d, segment, fn):
        self.fieldInfos = fn

        self.fieldsStream = d.openFile(segment + '.fdt')
        self.indexStream = d.openFile(segment + '.fdx')
                                      
        self.sze = self.indexStream.length / 8


    def close(self):
        self.fieldsStream.close()
        self.indexStream.close()


    def size(self):
        return self.sze


    def doc(self, n):
        self.indexStream.seek(n * 8L)
        position = self.indexStream.readLong()
        self.fieldsStream.seek(position)

        doc = document.Document()
        numFields = self.fieldsStream.readVInt()
        for i in range(numFields):
            fieldNumber = self.fieldsStream.readVInt()
            fi = self.fieldInfos.fieldInfoInt(fieldNumber)

            bits = self.fieldsStream.readByte()
            tokenized = ((bits & 1) != 0)

            doc.add(document.Field(fi.name, self.fieldsStream.readString(),
                          True, fi.isIndexed, tokenized))

        return doc

    
