# -*- coding: iso-8859-1 -*-
"""
MoinMoin - datastruct (dicts and groups) formatters

@copyright: 2009 MoinMoin:DmitrijsMilajevs
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin.formatter import FormatterBase
from MoinMoin import wikiutil

class GroupFormatter(FormatterBase):
    """
    Collect groups and format nothing
    """

    def __init__(self, request, **kw):
        FormatterBase.__init__(self, request, **kw)
        self.bullet_list_level = 0
        self.inside_list_item = False
        self.inside_link = False
        self.members = []
        self.new_member = ''
        self.new_link_member = ''

    def pagelink(self, on, pagename='', page=None, **kw):
        self.inside_link = on
        if self.inside_list_item:
            if not pagename and page:
                pagename = page.page_name
            pagename = wikiutil.normalize_pagename(pagename, self.request.cfg)
            self.new_link_member = pagename
        return ''

    def bullet_list(self, on, **kw):
        if on:
            self.bullet_list_level += 1
        else:
            self.bullet_list_level -= 1

        assert self.bullet_list_level >= 0
        return ''

    def listitem(self, on, **kw):
        if self.bullet_list_level == 1:
            self.inside_list_item = on
            if not on:
                if self.new_member.strip() == '' and self.new_link_member != '':
                    self.members.append(self.new_link_member.strip())
                if self.new_member != '' and self.new_link_member == '':
                    self.members.append(self.new_member.strip())
            self.new_member = ''
            self.new_link_member = ''
        return ''

    def definition_list(self, on, **kw):
        return ''

    def definition_term(self, on, compact=0, **kw):
        return ''

    def definition_desc(self, on, **kw):
        return ''

    def text(self, text, **kw):
        if self.inside_list_item and not self.inside_link:
            self.new_member += text
        return ''

    def null(self, *args, **kw):
        return ''

    # All these must be overriden here because they raise
    # NotImplementedError!@#! or return html?! in the base class.
    set_highlight_re = rawHTML = url = image = smiley = null
    strong = emphasis = underline = highlight = sup = sub = strike = null
    code = preformatted = small = big = code_area = code_line = null
    code_token = linebreak = paragraph = rule = icon = null
    number_list = null
    heading = table = null
    table_row = table_cell = attachment_link = attachment_image = attachment_drawing = null
    transclusion = transclusion_param = null

