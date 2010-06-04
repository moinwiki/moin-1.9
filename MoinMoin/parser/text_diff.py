# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Diff Parser - highlights diff tool output

    @copyright: 2006 Emilio Lopes, inspired by previous work
                done by Fabien Ninoles and Juergen Hermann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.parser._ParserBase import ParserBase

class Parser(ParserBase):
    parsername = "ColorizedDiff"
    extensions = ['.diff', '.patch', ]
    Dependencies = []

    def setupRules(self):
        ParserBase.setupRules(self)

        self.addRule("Comment", r'^(diff .*?)$')
        self.addRule("Comment", r'^(\*\*\* .*?)$')
        self.addRule("Comment", r'^(--- .*?)$')
        self.addRule("Comment", r'^(\+\+\+ .*?)$')
        self.addRule("Comment", r'^\*\*\*\*\*\*\*\*\*\*\*\*\*\*\* *$')

        self.addRule("DiffSeparator", r'^(@@ .*?)$')
        self.addRule("DiffSeparator", r'^--- *$')

        self.addRule("DiffAdded", r'^(\+.*?)$')
        self.addRule("DiffRemoved", r'^(-.*?)$')
        self.addRule("DiffAdded", r'^(>.*?)$')
        self.addRule("DiffRemoved", r'^(<.*?)$')
        self.addRule("DiffChanged", r'^(!.*?)$')

        self.addRuleFormat("DiffAdded")
        self.addRuleFormat("DiffRemoved")
        self.addRuleFormat("DiffChanged")
        self.addRuleFormat("DiffSeparator")

