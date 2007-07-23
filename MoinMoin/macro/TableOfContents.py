# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - TableOfContents Macro

    Optional integer argument: maximal depth of listing.

    @copyright: 2000-2002 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re, sha
from MoinMoin import config, wikiutil

#Dependencies = ["page"]
Dependencies = ["time"] # works around MoinMoinBugs/TableOfContentsLacksLinks

# from macro Include (keep in sync!)
_arg_heading = r'(?P<heading>,)\s*(|(?P<hquote>[\'"])(?P<htext>.+?)(?P=hquote))'
_arg_level = r',\s*(?P<level>\d*)'
_arg_from = r'(,\s*from=(?P<fquote>[\'"])(?P<from>.+?)(?P=fquote))?'
_arg_to = r'(,\s*to=(?P<tquote>[\'"])(?P<to>.+?)(?P=tquote))?'
_arg_sort = r'(,\s*sort=(?P<sort>(ascending|descending)))?'
_arg_items = r'(,\s*items=(?P<items>\d+))?'
_arg_skipitems = r'(,\s*skipitems=(?P<skipitems>\d+))?'
_arg_titlesonly = r'(,\s*(?P<titlesonly>titlesonly))?'
_arg_editlink = r'(,\s*(?P<editlink>editlink))?'
_args_re_pattern = r'^(?P<name>[^,]+)(%s(%s)?%s%s%s%s%s%s%s)?$' % (
    _arg_heading, _arg_level, _arg_from, _arg_to, _arg_sort, _arg_items,
    _arg_skipitems, _arg_titlesonly, _arg_editlink)

# from Include, too, but with extra htext group around header text
_title_re = r"^(?P<heading>(?P<hmarker>=+)\s(?P<htext>.*)\s(?P=hmarker))$"

class TableOfContents:
    """
    TOC Macro wraps all global variables without disturbing threads
    """

    def __init__(self, macro, args):
        self.macro = macro
        self._ = self.macro.request.getText

        self.inc_re = re.compile(r"^\[\[Include\((.*)\)\]\]")
        self.arg_re = re.compile(_args_re_pattern)
        self.head_re = re.compile(_title_re) # single lines only
        self.pre_re = re.compile(r'\{\{\{.+?\}\}\}', re.S)

        self.result = []
        self.baseindent = 0
        self.indent = 0
        self.lineno = 0
        self.titles = {}

        self.include_macro = None

        try:
            self.mindepth = int(macro.request.getPragma('section-numbers', 1))
        except (ValueError, TypeError):
            self.mindepth = 1

        try:
            self.maxdepth = max(int(args), 1)
        except (ValueError, TypeError):
            self.maxdepth = 99

    def IncludeMacro(self, *args, **kwargs):
        if self.include_macro is None:
            self.include_macro = wikiutil.importPlugin(self.macro.request.cfg,
                                                       'macro', "Include")
        return self.pre_re.sub('', self.include_macro(*args, **kwargs)).split('\n')

    def run(self):
        _ = self._
        self.result.append(self.macro.formatter.div(1, css_class="table-of-contents"))
        self.result.append(self.macro.formatter.paragraph(1, css_class="table-of-contents-heading"))
        self.result.append(self.macro.formatter.escapedText(_('Contents')))
        self.result.append(self.macro.formatter.paragraph(0))

        self.process_lines(self.pre_re.sub('', self.macro.parser.raw).split('\n'),
                           self.macro.formatter.page.page_name)
        # Close pending lists
        for dummy in range(self.baseindent, self.indent):
            self.result.append(self.macro.formatter.listitem(0))
            self.result.append(self.macro.formatter.number_list(0))
        self.result.append(self.macro.formatter.div(0))
        return ''.join(self.result)

    def process_lines(self, lines, pagename):
        for line in lines:
            # Filter out the headings
            self.lineno = self.lineno + 1
            match = self.inc_re.match(line)
            if match:
                # this is an [[Include()]] line.
                # now parse the included page and do the work on it.

                ## get heading and level from Include() line.
                tmp = self.arg_re.match(match.group(1))
                if tmp and tmp.group("name"):
                    inc_pagename = tmp.group("name")
                else:
                    # no pagename?  ignore it
                    continue
                if tmp.group("heading") and tmp.group("hquote"):
                    if tmp.group("htext"):
                        heading = tmp.group("htext")
                    else:
                        heading = inc_pagename
                    if tmp.group("level"):
                        level = int(tmp.group("level"))
                    else:
                        level = 1
                    inc_page_lines = ["%s %s %s" % ("=" * level, heading, "=" * level)]
                else:
                    inc_page_lines = []

                inc_page_lines = inc_page_lines + self.IncludeMacro(self.macro, match.group(1), called_by_toc=1)

                self.process_lines(inc_page_lines, inc_pagename)
            else:
                self.parse_line(line, pagename)

    def parse_line(self, line, pagename):
        # FIXME this also finds "headlines" in {{{ code sections }}}:
        match = self.head_re.match(line)
        if not match:
            return
        title_text = match.group('htext').strip()
        pntt = pagename + title_text
        self.titles.setdefault(pntt, 0)
        self.titles[pntt] += 1

        # Get new indent level
        newindent = len(match.group('hmarker'))
        if newindent > self.maxdepth or newindent < self.mindepth:
            return
        if not self.indent:
            self.baseindent = newindent - 1
            self.indent = self.baseindent

        # Close lists
        for dummy in range(0, self.indent-newindent):
            self.result.append(self.macro.formatter.listitem(0))
            self.result.append(self.macro.formatter.number_list(0))

        # Open Lists
        for dummy in range(0, newindent-self.indent):
            self.result.append(self.macro.formatter.number_list(1))
            self.result.append(self.macro.formatter.listitem(1))

        # Add the heading
        unique_id = ''
        if self.titles[pntt] > 1:
            unique_id = '-%d' % (self.titles[pntt], )

        # close last listitem if same level
        if self.indent == newindent:
            self.result.append(self.macro.formatter.listitem(0))

        if self.indent >= newindent:
            self.result.append(self.macro.formatter.listitem(1))
        self.result.append(self.macro.formatter.anchorlink(1,
            "head-" + sha.new(pntt.encode(config.charset)).hexdigest() + unique_id) +
                           self.macro.formatter.text(title_text) +
                           self.macro.formatter.anchorlink(0))

        # Set new indent level
        self.indent = newindent

def execute(macro, args):
    toc = TableOfContents(macro, args)
    return toc.run()

