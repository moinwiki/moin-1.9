# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Base Source Parser

    @copyright: 2002 by Taesu Pyo <bigflood@hitel.net>
    @license: GNU GPL, see COPYING for details.

    Docstrings and some refactoring by Oliver Graf <ograf@bitart.de>

basic css:

pre.codearea     { font-style: sans-serif; color: #000000; }

pre.codearea span.ID       { color: #000000; }
pre.codearea span.Char     { color: #004080; }
pre.codearea span.Comment  { color: #808080; }
pre.codearea span.Number   { color: #008080; font-weight: bold; }
pre.codearea span.String   { color: #004080; }
pre.codearea span.SPChar   { color: #0000C0; }
pre.codearea span.ResWord  { color: #4040ff; font-weight: bold; }
pre.codearea span.ConsWord { color: #008080; font-weight: bold; }

"""

import re, sha
from MoinMoin import config, wikiutil

def parse_start_step(request, args):
    """
    Parses common Colorizer parameters start, step, numbers.
    Uses L{wikiutil.parseAttributes} and sanitizes the results.

    Start and step must be a non negative number and default to 1,
    numbers might be on, off, or none and defaults to on. On or off
    means that numbers are switchable via JavaScript (html formatter),
    disabled means that numbers are disabled completely.

    attrdict is returned as last element in the tuple, to enable the
    calling parser to extract further arguments.

    @param request: a request instance
    @param args: the argument string

    @returns: numbers, start, step, attrdict
    """
    nums, start, step = 1, 1, 1
    attrs, msg = wikiutil.parseAttributes(request, args)
    if not msg:
        try:
            start = int(attrs.get('start','"1"')[1:-1])
        except ValueError:
            pass
        try:
            step = int(attrs.get('step','"1"')[1:-1])
        except ValueError:
            pass
        if attrs.get('numbers','"on"')[1:-1].lower() in ('off', 'false', 'no'):
            nums = 0
        elif attrs.get('numbers','"on"')[1:-1].lower() in ('none', 'disable'):
            nums = -1
    return nums, start, step, attrs

class FormatTextBase:
    pass

class FormatText(FormatTextBase):
    
    def __init__(self, fmt):
        self.fmt = fmt

    def formatString(self, formatter, word):
        return (formatter.code_token(1, self.fmt) +
                formatter.text(word) +
                formatter.code_token(0, self.fmt))

class FormatTextID(FormatTextBase):
    
    def __init__(self, fmt, icase=0):
        if not isinstance(fmt, FormatText):
            self.def_fmt = FormatText(fmt)
        else:
            self.def_fmt = fmt
        self._ignore_case = icase
        self.fmt = {}

    def addFormat(self, word, fmt):
        if self._ignore_case:
            word = word.lower()
        self.fmt[word] = fmt
        
    def setDefaultFormat(self, fmt):
        self.def_fmt = fmt
        
    def formatString(self, formatter, word):
        if self._ignore_case:
            sword = word.lower()
        else:
            sword = word
        return self.fmt.get(sword, self.def_fmt).formatString(formatter, word)

class FormattingRuleSingle:
    
    def __init__(self, name, str_re, icase=0):
        self.name = name
        self.str_re = str_re
        
    def getStartRe(self):
        return self.str_re
    
    def getText(self, parser, hit):
        return hit

class FormattingRulePair:
    
    def __init__(self, name, str_begin, str_end, icase=0):
        self.name = name
        self.str_begin = str_begin
        self.str_end = str_end
        if icase:
            self.end_re = re.compile(str_end, re.M|re.I)
        else:
            self.end_re = re.compile(str_end, re.M)
        
    def getStartRe(self):
        return self.str_begin
    
    def getText(self, parser, hit):
        match = self.end_re.search(parser.line, parser.lastpos)
        if not match:
            next_lastpos = len(parser.line)
        else:
            next_lastpos = match.end() + (match.end() == parser.lastpos)
        r = parser.line[parser.lastpos:next_lastpos]
        parser.lastpos = next_lastpos
        return hit + r


# ------------------------------------------------------------------------

class ParserBase:

    parsername = 'ParserBase'
    
    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request
        self.show_nums, self.num_start, self.num_step, attrs = parse_start_step(request, kw.get('format_args',''))

        self._ignore_case = 0
        self._formatting_rules = []
        self._formatting_rules_n2r = {}
        self._formatting_rule_index = 0
        self.rule_fmt = {}
        self.line_count = len(raw.split('\n'))+1

    def setupRules(self):
        self.def_format = FormatText('Default')
        self.ID_format = FormatTextID('ID', self._ignore_case)
        self.addRuleFormat("ID", self.ID_format)
        self.addRuleFormat("Operator")
        self.addRuleFormat("Char")
        self.addRuleFormat("Comment")
        self.addRuleFormat("Number")
        self.addRuleFormat("String")
        self.addRuleFormat("SPChar")
        self.addRuleFormat("ResWord")
        self.addRuleFormat("ResWord2")
        self.addRuleFormat("ConsWord")
        self.addRuleFormat("Special")
        self.addRuleFormat("Preprc")
        self.addRuleFormat("Error")
        self.reserved_word_format = FormatText('ResWord')
        self.constant_word_format = FormatText('ConsWord')

    def addRule(self, name, str_re):
        self._formatting_rule_index += 1
        n = "%s_%s" % (name, self._formatting_rule_index)
        f = FormattingRuleSingle(name, str_re, self._ignore_case)
        self._formatting_rules.append((n, f))
        self._formatting_rules_n2r[n] = f

    def addRulePair(self, name, start_re, end_re):
        self._formatting_rule_index += 1
        n = "%s_%s" % (name, self._formatting_rule_index)
        f = FormattingRulePair(name, start_re, end_re, self._ignore_case)
        self._formatting_rules.append((n, f))
        self._formatting_rules_n2r[n] = f

    def addWords(self, words, fmt):
        if not isinstance(fmt, FormatTextBase):
            fmt = FormatText(fmt)
        for w in words:
            self.ID_format.addFormat(w, fmt)

    def addReserved(self, words):
        self.addWords(words, self.reserved_word_format)

    def addConstant(self, words):
        self.addWords(words, self.constant_word_format)
        
    def addRuleFormat(self, name, fmt=None):
        if fmt is None:
            fmt = FormatText(name)
        self.rule_fmt[name] = fmt

    def format(self, formatter, form = None):
        """ Send the text.
        """

        self.setupRules()

        l = []
        for n, f in self._formatting_rules:
            l.append("(?P<%s>%s)" % (n, f.getStartRe()))
        
        if self._ignore_case:
            scan_re = re.compile("|".join(l), re.M|re.I)
        else:
            scan_re = re.compile("|".join(l), re.M)

        self.lastpos = 0
        self.line = self.raw

        self._code_id = sha.new(self.raw.encode(config.charset)).hexdigest()
        self.request.write(formatter.code_area(1, self._code_id, self.parsername, self.show_nums, self.num_start, self.num_step))

        self.request.write(formatter.code_line(1))
            #formatter, len('%d' % (self.line_count,)))
        
        match = scan_re.search(self.line)

        while match and self.lastpos < len(self.line):
            # add the match we found
            self.write_normal_text(formatter,
                                   self.line[self.lastpos:match.start()])
            self.lastpos = match.end() + (match.end() == self.lastpos)

            self.write_match(formatter, match)

            # search for the next one
            match = scan_re.search(self.line, self.lastpos)

        self.write_normal_text(formatter, self.line[self.lastpos:])

        self.request.write(formatter.code_area(0, self._code_id))


    def write_normal_text(self, formatter, text):
        first = 1
        for line in text.expandtabs(4).split('\n'):
            if not first:
                self.request.write(formatter.code_line(1))
            else:
                first = 0
            self.request.write(formatter.text(line))

    def write_match(self, formatter, match):
        for n, hit in match.groupdict().items():
            if not hit:
                continue
            r = self._formatting_rules_n2r[n]
            s = r.getText(self, hit)
            c = self.rule_fmt.get(r.name, None)
            if not c:
                c = self.def_format
            first = 1
            for line in s.expandtabs(4).split('\n'):
                if not first:
                    self.request.write(formatter.code_line(1))
                else:
                    first = 0
                self.request.write(c.formatString(formatter, line))
