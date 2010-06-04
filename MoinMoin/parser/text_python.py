# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - highlighting Python Source Parser

    @copyright: 2001 Juergen Hermann <jh@web.de>,
                2006-2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import StringIO
import keyword, token, tokenize

from MoinMoin import config, wikiutil
from MoinMoin.parser._ParserBase import parse_start_step
from MoinMoin.support.python_compatibility import hash_new

_KEYWORD = token.NT_OFFSET + 1
_TEXT = token.NT_OFFSET + 2

_tokens = {
    token.NUMBER: 'Number',
    token.OP: 'Operator',
    token.STRING: 'String',
    tokenize.COMMENT: 'Comment',
    token.NAME: 'ID',
    token.ERRORTOKEN: 'Error',
    _KEYWORD: 'ResWord',
    _TEXT: 'Text',
}

Dependencies = ['user'] # the "Toggle line numbers link" depends on user's language

class Parser:
    """ Send colored python source.
    """

    extensions = ['.py']
    Dependencies = Dependencies

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

        self.result = [] # collects output

        self._code_id = hash_new('sha1', self.raw.encode(config.charset)).hexdigest()
        self.result.append(formatter.code_area(1, self._code_id, 'ColorizedPython', self.show_num, self.num_start, self.num_step))
        self.formatter = formatter
        self.result.append(formatter.code_line(1))
        #len('%d' % (len(self.lines)-1, )))

        # parse the source and write it
        self.pos = 0
        text = StringIO.StringIO(self.raw)
        try:
            tokenize.tokenize(text.readline, self)
        except IndentationError, ex:
            msg = ex[0]
            errmsg = (self.formatter.linebreak() +
                      self.formatter.strong(1) + "ERROR: %s" % msg + self.formatter.strong(0) +
                      self.formatter.linebreak())
            self.result.append(errmsg)
        except tokenize.TokenError, ex:
            msg = ex[0]
            line = ex[1][0]
            errmsg = (self.formatter.linebreak() +
                      self.formatter.strong(1) + "ERROR: %s" % msg + self.formatter.strong(0) +
                      self.formatter.linebreak() +
                      wikiutil.escape(self.raw[self.lines[line]:]))
            self.result.append(errmsg)
        self.result.append(self.formatter.code_line(0))
        self.result.append(formatter.code_area(0, self._code_id))
        self.request.write(''.join(self.result))

    def __call__(self, toktype, toktext, (srow, scol), (erow, ecol), line):
        """ Token handler.
        """
        # calculate new positions
        oldpos = self.pos
        newpos = self.lines[srow] + scol
        self.pos = newpos + len(toktext)

        # handle newlines
        if toktype in [token.NEWLINE, tokenize.NL]:
            self.result.append(self.formatter.code_line(0))
            self.result.append(self.formatter.code_line(1))
            return

        # send the original whitespace, if needed
        if newpos > oldpos:
            self.result.append(self.formatter.text(self.raw[oldpos:newpos]))

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
        first = True
        for part in toktext.split('\n'):
            if not first:
                self.result.append(self.formatter.code_line(0))
                self.result.append(self.formatter.code_line(1))
            else:
                first = False
            self.result.append(self.formatter.code_token(1, tokid) +
                               self.formatter.text(part) +
                               self.formatter.code_token(0, tokid))

