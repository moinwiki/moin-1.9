# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - TableOfContents Macro

    @copyright: 2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

import re
from MoinMoin.formatter import FormatterBase
from MoinMoin.Page import Page
from MoinMoin import wikiutil


Dependencies = ['page']

class TOCFormatter(FormatterBase):
    def __init__(self, request, **kw):
        FormatterBase.__init__(self, request, **kw)
        self.in_heading = False
        self.collected_headings = request._tocfm_collected_headings

    def _text(self, text):
        if self.in_heading:
            self.collected_headings[-1][2] += text
        return text

    def heading(self, on, depth, **kw):
        id = kw.get('id', '')
        self.in_heading = on
        if on:
            self.collected_headings.append([depth, id, u''])
        return ''

    def macro(self, macro_obj, name, args):
        try:
            # plugins that are defined in the macro class itself
            # can't generate headings this way, but that's fine
            gen_headings = wikiutil.importPlugin(self.request.cfg, 'macro',
                                                 name, 'generates_headings')
            if gen_headings:
                return FormatterBase.macro(self, macro_obj, name, args)
        except (wikiutil.PluginMissingError, wikiutil.PluginAttributeError):
            pass
        return ''

    def _anything_return_empty(self, *args, **kw):
        return ''

    lang = _anything_return_empty
    sysmsg = _anything_return_empty
    startDocument = _anything_return_empty
    endDocument = _anything_return_empty
    startContent = _anything_return_empty
    endContent = _anything_return_empty
    pagelink = _anything_return_empty
    interwikilink = _anything_return_empty
    url = _anything_return_empty
    attachment_link = _anything_return_empty
    attachment_image = _anything_return_empty
    attachment_drawing = _anything_return_empty
    attachment_inlined = _anything_return_empty
    anchordef = _anything_return_empty
    line_anchordef = _anything_return_empty
    anchorlink = _anything_return_empty
    line_anchorlink = _anything_return_empty
    image = _anything_return_empty
    smiley = _anything_return_empty
    nowikiword = _anything_return_empty
    strong = _anything_return_empty
    emphasis = _anything_return_empty
    underline = _anything_return_empty
    highlight = _anything_return_empty
    sup = _anything_return_empty
    sub = _anything_return_empty
    strike = _anything_return_empty
    code = _anything_return_empty
    preformatted = _anything_return_empty
    small = _anything_return_empty
    big = _anything_return_empty
    code_area = _anything_return_empty
    code_line = _anything_return_empty
    code_token = _anything_return_empty
    linebreak = _anything_return_empty
    paragraph = _anything_return_empty
    rule = _anything_return_empty
    icon = _anything_return_empty
    number_list = _anything_return_empty
    bullet_list = _anything_return_empty
    listitem = _anything_return_empty
    definition_list = _anything_return_empty
    definition_term = _anything_return_empty
    definition_desc = _anything_return_empty
    table = _anything_return_empty
    table_row = _anything_return_empty
    table_cell = _anything_return_empty
    _get_bang_args = _anything_return_empty
    parser = _anything_return_empty
    div = _anything_return_empty
    span = _anything_return_empty
    rawHTML = _anything_return_empty
    escapedText = _anything_return_empty
    comment = _anything_return_empty

def macro_TableOfContents(macro, maxdepth=int):
    """
Prints a table of contents.

 maxdepth:: maximum depth the table of contents is generated for (defaults to unlimited)
    """
    if maxdepth is None:
        maxdepth = 99

    pname = macro.formatter.page.page_name

    macro.request._tocfm_collected_headings = []
    tocfm = TOCFormatter(macro.request)
    p = Page(macro.request, pname, formatter=tocfm, rev=macro.request.rev)
    output = macro.request.redirectedOutput(p.send_page,
                                            content_only=True,
                                            count_hit=False,
                                            omit_footnotes=True)

    _ = macro.request.getText

    result = [
        macro.formatter.div(1, css_class="table-of-contents"),
        macro.formatter.paragraph(1, css_class="table-of-contents-heading"),
        macro.formatter.text(_('Contents', formatted=False)),
        macro.formatter.paragraph(0),
    ]

    lastlvl = 0

    for lvl, id, txt in macro.request._tocfm_collected_headings:
        if lvl > maxdepth or not id:
            continue
        while lastlvl > lvl:
            result.append(macro.formatter.number_list(0))
            lastlvl -= 1
        while lastlvl < lvl:
            result.append(macro.formatter.number_list(1))
            lastlvl += 1
        result.extend([
            macro.formatter.listitem(1),
            macro.formatter.anchorlink(1, id),
            macro.formatter.text(txt),
            macro.formatter.anchorlink(0),
            macro.formatter.listitem(0),
        ])

    result.append(macro.formatter.div(0))
    return ''.join(result)
