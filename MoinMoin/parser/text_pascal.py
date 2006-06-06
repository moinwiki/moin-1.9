# -*- coding: iso-8859-1 -*-
"""
	MoinMoin - Pascal Source Parser

    @copyright: 2004-2005 by Johannes Berg <johannes@sipsolutions.net>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.parser.ParserBase import ParserBase

Dependencies = []

class Parser(ParserBase):

    parsername = 'ColorizedPascal'
    extensions = ['.pas']
    Dependencies = []

    def __init__(self, raw, request, **kw):
        ParserBase.__init__(self,raw,request,**kw)
        self._ignore_case = 1

    def setupRules(self):
        ParserBase.setupRules(self)
        
        self.addRulePair("Comment","\(\*","\*\)")
        self.addRulePair("Comment","\{","\}")
        self.addRule("Comment","//.*$")
        self.addRulePair("String",'\'','\'')
        self.addRule("Char",r"'\\.'|#[a-f0-9][a-f0-9]")
        self.addRule("Number",r"[0-9](\.[0-9]*)?(eE[+-][0-9])?|\$[0-9a-fA-F]+")
        self.addRule("ID","[a-zA-Z_][0-9a-zA-Z_]*")
        self.addRule("SPChar",r"[~!%^&*()+=|\[\]:;,.<>/?{}-]")
        
        reserved_words = ['class','interface','set','uses','unit',
                          'byte','integer','longint','float','double',
                          'extended','char','shortint','boolean',
                          'var','const','private','public','protected',
                          'new','this','super','abstract','native',
                          'synchronized','transient','volatile','strictfp',
                          'if','else','while','for','do','case','default',
                          'try','except','finally','raise','continue','break',
                          'begin','end','type','class','implementation',
                          'procedure','function','constructor','destructor']
        
        self.addReserved(reserved_words)
        
        constant_words = ['true','false','nil']
        
        self.addConstant(constant_words)
