# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.formatter.dicts

    @copyright: 2005 MoinMoin:NirSoffer
                2009 MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""


from MoinMoin.formatter import FormatterBase
from MoinMoin import wikiutil


class Formatter(FormatterBase):
    """
    Collect definition lists and format nothing
    """

    def __init__(self, request, **kw):
        FormatterBase.__init__(self, request, **kw)
        self.dict = {}
        self.term = []
        self.description = []
        self.current = None

    def definition_term(self, on):
        if on:
            self.term = []
            self.current = 'term'
        else:
            self.current = None
        return self.null()

    def definition_desc(self, on):
        if on:
            self.description = []
            self.current = 'description'
        else:
            term = ' '.join(self.term)
            description = ' '.join(self.description)
            self.dict[term] = description
            self.current = None
        return self.null()

    def text(self, text):
        if self.current:
            text = text.strip()
            if text:
                attr = getattr(self, self.current)
                attr.append(text)
        return self.null()

    def null(self, *args, **kw):
        return ''

    # All these must be overriden here because they raise
    # NotImplementedError!@#! or return html?! in the base class.
    set_highlight_re = rawHTML = url = image = smiley = null
    strong = emphasis = underline = highlight = sup = sub = strike = null
    code = preformatted = small = big = code_area = code_line = null
    code_token = linebreak = paragraph = rule = icon = null
    number_list = definition_list = bullet_list = listitem = null
    heading = table = pagelink = null
    table_row = table_cell = attachment_link = attachment_image = attachment_drawing = null
    transclusion = transclusion_param = null

