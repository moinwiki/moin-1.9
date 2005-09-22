# -*- test-case-name: lupy.test.test_document -*-
"""Documents and Fields"""
# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

class Document(object):
    """Documents are the unit of indexing and search.

    A Document is a set of fields.  Each field has a name and a textual
    value.  A field may be stored with the document, in which case it is
    returned with search hits on the document.  Thus each document should
    typically contain stored fields which uniquely identify it.
    """

    def __init__(self):
        self._fields = {}
        self.fieldNames = []
    
    def add(self, field):
        """Adds a field to a document."""
        name = field.name()
        self._fields[name] = field
        if name not in self.fieldNames:
            self.fieldNames.append(name)
    
    def getField(self, name):
        """Returns a field with the given name, or None if none exist."""
        return self._fields.get(name, None)

    def get(self, name):
        """Returns the string value of a field, or None."""
        field = self.getField(name)
        if field is not None:
            return field.stringValue()
        else:
            return None

    def fields(self):
        """Return Python iterator over fields."""
        return [self._fields[name] for name in self.fieldNames]

    def __repr__(self):
        return '<Document[%s]>' % ("|".join(self.fieldNames),)


class Field(object):
    """A field is a section of a Document.

    Each field has two parts, a name and a value.  Values may be free
    text, provided as a string or as a file, or they may be atomic
    keywords, which are not further processed.  Such keywords may be used
    to represent dates, urls, etc.  Fields are optionally stored in the
    index, so that they may be returned with hits on the document.
    """

    def __init__(self, name, string, store=False, index=True, token=True):
        self.nom = name
        self.stringVal = string
        self.readerVal = None
        self.isStored = store
        self.isIndexed = index
        self.isTokenized = token        

    def __repr__(self):
        if self.isStored and self.isIndexed and not self.isTokenized:
            return '<Keyword<' + self.nom + ':' + self.stringVal + '>>'
        elif self.isStored and not self.isIndexed and not self.isTokenized:
            return '<Unindexed<' + self.nom + ':' + self.stringVal + '>>'
        elif self.isStored and self.isIndexed and self.isTokenized and self.stringVal is not None:
            return '<Text<' + self.nom + ':' + self.stringVal + '>>'
        elif self.isStored and self.isIndexed and self.isTokenized and self.stringVal is not None:
            return '<Text<' + self.nom + ':' + self.readerVal + '>>'
        else:
            return '<Field<???>'

    def name(self):
        return self.nom

    def stringValue(self):
        return self.stringVal

    def readerValue(self):
        return self.readerVal


def Keyword(name, value):
    "An untokenized field that is included in the index and returned with search results."
    return Field(name, value, True, True, False)


def Text(name, strOrFile, store=True):
    """A tokenized field that is included in the index and returned
    with search results.  Accepts string or file-like object."""
    if isinstance(strOrFile, (str, unicode)):
        res = Field(name, strOrFile, store, True, True)
    else:
        res = Field(name, None)
        res.readerVal = strOrFile
        res.stringVal = None
    return res


def UnIndexed(name, value):
    return Field(name, value, True, False, False)


def UnStored(name, value):
    return Field(name, value, False, True, True)
