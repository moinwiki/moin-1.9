# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "text/plain" Formatter

    @copyright: 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.formatter.base import FormatterBase

class Formatter(FormatterBase):
    """
        Send plain text data.
    """

    hardspace = u' '

    def __init__(self, request, **kw):
        apply(FormatterBase.__init__, (self, request), kw)
        self._in_code_area = 0
        self._in_code_line = 0
        self._code_area_state = [0, -1, -1, 0]
        self._in_list = 0
        self._did_para = 0
        self._url = None
        self._text = None # XXX does not work with links in headings!!!!!

    def startDocument(self, pagename):
        line = u"*" * (len(pagename)+2) + u'\n'
        return u"%s %s \n%s" % (line, pagename, line)

    def endDocument(self):
        return u'\n'

    def sysmsg(self, on, **kw):
        return (u'\n\n*** ', u' ***\n\n')[not on]

    def pagelink(self, on, pagename='', page=None, **kw):
        apply(FormatterBase.pagelink, (self, on, pagename, page), kw)
        return (u">>", u"<<") [not on]

    def interwikilink(self, on, interwiki='', pagename='', **kw):
        if on:
            self._url = u"%s:%s" % (interwiki, pagename)
            self._text = []
            return u''
        else:
            if "".join(self._text) == self._url:
                self._url = None
                self._text = None
                return ''
            else:
                self._url = None
                self._text = None
                return u' [%s]' % (self._url)
            
    def url(self, on, url='', css=None, **kw):
        if on:
            self._url = url
            self._text = []
            return u''
        else:
            if "".join(self._text) == self._url:
                self._url = None
                self._text = None
                return ''
            else:
                self._url = None
                self._text = None
                return u' [%s]' % (self._url)

    # Attachments ######################################################

    def attachment_link(self, url, text, **kw):
        return "[%s]" % text
    def attachment_image(self, url, **kw):
        return "[image:%s]" % url

    def attachment_drawing(self, url, text, **kw):
        return "[drawing:%s]" % text
    
    def text(self, text):
        self._did_para = 0
        if self._text is not None:
            self._text.append(text)
        return text

    def rule(self, size=0):
        size = min(size, 10)
        ch = u"---~=*+#####"[size]
        return (ch * 79) + u'\n'

    def strong(self, on):
        return u'*'

    def emphasis(self, on):
        return u'/'

    def highlight(self, on):
        return u''

    def number_list(self, on, type=None, start=None):
        if on:
            self._in_list = 1
            return [u'\n', u'\n\n'][not self._did_para]
        else:
            self._in_list = 0
            if not self._did_para:
                self._did_para = 1
                return u'\n'
        return u''

    def bullet_list(self, on):
        if on:
            self._in_list = -1
            return [u'\n', u'\n\n'][not self._did_para]
        else:
            self._in_list = 0
            if not self._did_para:
                self._did_para = 1
                return u'\n'
        return u''

    def listitem(self, on, **kw):
        if on:
            if self._in_list>0:
                self._in_list += 1
                self._did_para = 1
                return ' %d. ' % (self._in_list-1,)
            elif self._in_list<0:
                self._did_para = 1
                return u' * '
            else:
                return u' * '
        else:
            self._did_para = 1
            return u'\n'
        
    def sup(self, on):
        return u'^'

    def sub(self, on):
        return u'_'

    def code(self, on, **kw):
        #return [unichr(0x60), unichr(0xb4)][not on]
        return u"'" # avoid high-ascii

    def preformatted(self, on):
        FormatterBase.preformatted(self, on)
        snip = u'---%<'
        snip = snip + (u'-' * (78 - len(snip)))
        if on:
            return u'\n' + snip + u'\n'
        else:
            return snip + u'\n'

    def small(self, on):
        return u''

    def big(self, on):
        return u''

    def code_area(self, on, code_id, code_type='code', show=0, start=-1, step=-1):
        snip = u'---CodeArea'
        snip = snip + (u'-' * (78 - len(snip)))
        if on:
            self._in_code_area = 1
            self._in_code_line = 0
            self._code_area_state = [show, start, step, start]
            return u'\n' + snip + u'\n'
        else:
            if self._in_code_line:
                return self.code_line(0) + snip + u'\n'
            return snip + u'\n'

    def code_line(self, on):
        res = u''
        if not on or (on and self._in_code_line):
            res += u'\n'
        if on:
            if self._code_area_state[0]>0:
                res += u' %4d  ' % ( self._code_area_state[3] )
                self._code_area_state[3] += self._code_area_state[2]
        self._in_code_line = on != 0
        return res

    def code_token(self, on, tok_type):
        return ""

    def paragraph(self, on):
        FormatterBase.paragraph(self, on)
        if self._did_para:
            on = 0
        return [u'\n', u''][not on]

    def linebreak(self, preformatted=1):
        return u'\n'

    def smiley(self, text):
        return text

    def heading(self, on, depth, **kw):
        if on:
            self._text = []
            return '\n\n'
        else:
            result =  u'\n%s\n\n' % (u'=' * len("".join(self._text)))
            self._text = None
            return result

    def table(self, on, attrs={}):
        return u''

    def table_row(self, on, attrs={}):
        return u''

    def table_cell(self, on, attrs={}):
        return u''

    def underline(self, on):
        return u'_'

    def definition_list(self, on):
        return u''

    def definition_term(self, on, compact=0):
        result = u''
        if not compact: result = result + u'\n'
        if not on: result = result + u':\n'
        return result

    def definition_desc(self, on):
        return [u'    ', u'\n'][not on]

    def image(self, **kw):
        if kw.has_key(u'alt'):
            return kw[u'alt']
        return u''

    def lang(self, on, lang_name):
        return ''
