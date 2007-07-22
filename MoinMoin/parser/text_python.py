# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - highlighting Python Source Parser

    @copyright: 2001 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import StringIO
import keyword, token, tokenize, sha
from MoinMoin import config, wikiutil
from MoinMoin.parser._ParserBase import parse_start_step

_KEYWORD = token.NT_OFFSET + 1
_TEXT    = token.NT_OFFSET + 2

_tokens = {
    token.NUMBER:       'Number',
    token.OP:           'Operator',
    token.STRING:       'String',
    tokenize.COMMENT:   'Comment',
    token.NAME:         'ID',
    token.ERRORTOKEN:   'Error',
    _KEYWORD:           'ResWord',
    _TEXT:              'Text',
}

Dependencies = []

class Parser:
    """ Send colored python source.
    """

    extensions = ['.py']
    Dependencies = []

    def __init__(self, raw, request, **kw):
        """ Store the source text.
        """
        self.raw = raw.expandtabs().rstrip()
        self.request = request
        self.form = request.form
        self._ = request.getText

        self.show_num, self.num_start, self.num_step, attrs = parse_start_step(request, kw.get('format_args', ''))

    def format(self, formatter):
        """ Parse and send the colored source.
        """
        # store line offsets in self.lines
        self.lines = [0, 0]
        pos = 0
        while 1:
            try:
                pos = self.raw.index('\n', pos) + 1
            except ValueError:
                break
            self.lines.append(pos)
        self.lines.append(len(self.raw))

        self._code_id = sha.new(self.raw.encode(config.charset)).hexdigest()
        self.request.write(formatter.code_area(1, self._code_id, 'ColorizedPython', self.show_num, self.num_start, self.num_step))
        self.formatter = formatter
        self.request.write(formatter.code_line(1))
        #len('%d' % (len(self.lines)-1, )))

        # parse the source and write it
        self.pos = 0
        text = StringIO.StringIO(self.raw)
        try:
            tokenize.tokenize(text.readline, self)
        except tokenize.TokenError, ex:
            msg = ex[0]
            line = ex[1][0]
            errmsg = (self.formatter.linebreak() +
                      self.formatter.strong(1) + "ERROR: %s" % msg + self.formatter.strong(0) +
                      self.formatter.linebreak() +
                      wikiutil.escape(self.raw[self.lines[line]:]))
            self.request.write(errmsg)
        self.request.write(self.formatter.code_line(0))
        self.request.write(formatter.code_area(0, self._code_id))

    def __call__(self, toktype, toktext, (srow, scol), (erow, ecol), line):
        """ Token handler.
        """
        # calculate new positions
        oldpos = self.pos
        newpos = self.lines[srow] + scol
        self.pos = newpos + len(toktext)

        # handle newlines
        if toktype in [token.NEWLINE, tokenize.NL]:
            self.request.write(self.formatter.code_line(0))
            self.request.write(self.formatter.code_line(1))
            return

        # send the original whitespace, if needed
        if newpos > oldpos:
            self.request.write(self.formatter.text(self.raw[oldpos:newpos]))

        # skip indenting tokens
        if toktype in [token.INDENT, token.DEDENT]:
            self.pos = newpos
            return

        # map token type to a color group
        if token.LPAR <= toktype and toktype <= token.OP:
            toktype = token.OP
        elif toktype == token.NAME and keyword.iskeyword(toktext):
            toktype = _KEYWORD
        tokid = _tokens.get(toktype, _tokens[_TEXT])

        # send text
        first = 1
        for part in toktext.split('\n'):
            if not first:
                self.request.write(self.formatter.code_line(0))
                self.request.write(self.formatter.code_line(1))
            else:
                first = 0
            self.request.write(self.formatter.code_token(1, tokid) +
                               self.formatter.text(part) +
                               self.formatter.code_token(0, tokid))

