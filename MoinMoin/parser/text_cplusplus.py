# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - C++ Source Parser

    @copyright: 2002 Taesu Pyo <bigflood@hitel.net>
    @license: GNU GPL, see COPYING for details.

css:

pre.cpparea     { font-style: sans-serif; color: #000000; }

pre.cpparea span.ID       { color: #000000; }
pre.cpparea span.Char     { color: #004080; }
pre.cpparea span.Comment  { color: #808080; }
pre.cpparea span.Number   { color: #008080; font-weight: bold; }
pre.cpparea span.String   { color: #004080; }
pre.cpparea span.SPChar   { color: #0000C0; }
pre.cpparea span.ResWord  { color: #4040ff; font-weight: bold; }
pre.cpparea span.ConsWord { color: #008080; font-weight: bold; }
pre.cpparea span.ResWord2 { color: #0080ff; font-weight: bold; }
pre.cpparea span.Special  { color: #0000ff; }
pre.cpparea span.Preprc   { color: #804000; }

"""

from MoinMoin.parser._ParserBase import ParserBase

Dependencies = ['user'] # the "Toggle line numbers link" depends on user's language

class Parser(ParserBase):

    parsername = "ColorizedCPlusPlus"
    extensions = ['.c', '.h', '.cpp', '.c++']
    Dependencies = Dependencies

    def setupRules(self):
        ParserBase.setupRules(self)

        self.addRulePair("Comment", r"/[*]", r"[*]/")
        self.addRule("Comment", r"//.*$")
        self.addRulePair("String", r'L?"', r'$|[^\\](\\\\)*"')
        self.addRule("Char", r"'\\.'|'[^\\]'")
        self.addRule("Number", r"[0-9](\.[0-9]*)?(eE[+-][0-9])?[flFLdD]?|0[xX][0-9a-fA-F]+[Ll]?")
        self.addRule("Preprc", r"^\s*#(.*\\\n)*(.*(?!\\))$")
        self.addRule("ID", r"[a-zA-Z_][0-9a-zA-Z_]*")
        self.addRule("SPChar", r"[~!%^&*()+=|\[\]:;,.<>/?{}-]")

        reserved_words = ['struct', 'class', 'union', 'enum',
        'int', 'float', 'double', 'signed', 'unsigned', 'char', 'short', 'void', 'bool',
        'long', 'register', 'auto', 'operator',
        'static', 'const', 'private', 'public', 'protected', 'virtual', 'explicit',
        'new', 'delete', 'this',
        'if', 'else', 'while', 'for', 'do', 'switch', 'case', 'default', 'sizeof',
        'dynamic_cast', 'static_cast', 'const_cast', 'reinterpret_cast', 'typeid',
        'try', 'catch', 'throw', 'throws', 'return', 'continue', 'break', 'goto']

        reserved_words2 = ['extern', 'volatile', 'typedef', 'friend',
                           '__declspec', 'inline', '__asm', 'thread', 'naked',
                           'dllimport', 'dllexport', 'namespace', 'using',
                           'template', 'typename', 'goto']

        special_words = ['std', 'string', 'vector', 'map', 'set', 'cout', 'cin', 'cerr', 'endl']
        constant_words = ['true', 'false', 'NULL']

        self.addReserved(reserved_words)
        self.addConstant(constant_words)

        self.addWords(reserved_words2, 'ResWord2')
        self.addWords(special_words, 'Special')

