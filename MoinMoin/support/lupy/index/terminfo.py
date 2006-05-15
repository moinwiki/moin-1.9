# This module is part of the Lupy project and is Copyright 2003 Amir
# Bakhtiar (amir@divmod.org). This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

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

    
