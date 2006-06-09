# This module is part of the Lupy project and is Copyright 2005 Florian
# Festi. This is free software; you can redistribute
# it and/or modify it under the terms of version 2.1 of the GNU Lesser
# General Public License as published by the Free Software Foundation.

import re

def re_prefix(regex):
    """
    return a string that the beginning of regex that will always match
    Assumes the regex is a valid regular expression!!!
    """
    match = re.search(r"[[({\\.$*+?|]", regex)
    if not match: return regex

    if regex.find("|") != -1:
        # XXXX use string or RE to group non special chars
        # States
        plain = 0
        escape = 1
        charset = 2
        charsetfirst = 3
        charsetescape = 4
            
        state = plain
        parenthesis = 0
        for c in regex:
            if state == plain:
                if c == "\\": state = escape
                elif c == "(": parenthesis += 1
                elif c == ")": parenthesis -= 1
                elif c == "[": state = charsetfirst
                elif c == "|":
                    if parenthesis == 0:
                        # | on toplevel
                        return ""
            elif state == charset:
                if c == "]": state = plain
                elif c == "\\": state = charsetescape
            elif state == charsetfirst:
                if c == "\\": state = charsetescape
                else: state = charset                
            elif state == charsetescape: state = charset
            elif state == escape:
                state = plain

    end = match.start()
    if match.group() in "*{?": end -= 1 # RE element refere to last char
    return regex[:end]

from term import TermQuery
from boolean import BooleanQuery
from MoinMoin.support.lupy.index.term import Term

class RegularExpressionQuery(TermQuery):
    """Matches all documents that contain a word match the
    regular expression (RE) handed over as text of the term.
    This query is reasonably fast if the RE starts with normal chars.
    If the RE starts with RE special chars the whole index is searched!
    The RE is MATCHED against the terms in the documents!
    """
    def sumOfSquaredWeights(self, searcher):
        self.query = BooleanQuery()
        reader = searcher.reader

        needle = self.term.text()
        prefix = re_prefix(needle)
        reg_ex = re.compile(needle, re.U)
        field = self.term.field()

        ts = reader.terms(Term(field, prefix))

        while True:
            if reg_ex.match(ts.term.text()) and ts.term.field()==field:
                self.query.add(TermQuery(ts.term), False, False)
            if not ts.term.text().startswith(prefix):
                break
            try:
                ts.next()
            except StopIteration:
                break
        return  self.query.sumOfSquaredWeights(searcher)

    def scorer(self, reader):
        return self.query.scorer(reader)
            
