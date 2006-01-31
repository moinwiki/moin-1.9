# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - pagelinks Formatter

    @copyright: 2005 Nir Soffer <nirs@freeshell.org>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.formatter.base import FormatterBase

class Formatter(FormatterBase):
    """ Collect pagelinks and format nothing :-) """        
    
    def pagelink(self, on, pagename='', page=None, **kw):
        FormatterBase.pagelink(self, on, pagename, page, **kw)
        return self.null()
 
    def null(self, *args, **kw):
        return ''
    
    # All these must be overriden here because they raise
    # NotImplementedError!@#! or return html?! in the base class.
    set_highlight_re = null
    url = null
    image = null
    smiley = null
    text = null
    strong = null
    emphasis = null
    underline = null
    highlight = null
    sup = null
    sub = null
    strike = null
    code = null
    preformatted = null
    small = null
    big = null
    code_area = null
    code_line = null
    code_token = null
    linebreak = null
    paragraph = null
    rule = null
    icon = null
    number_list = null
    bullet_list = null
    listitem = null
    definition_list = null
    definition_term = null
    definition_desc = null
    heading = null
    table = null
    table_row = null
    table_cell = null
    attachment_link = null
    attachment_image = null
    attachment_drawing = null

