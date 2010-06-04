# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - IRC Log Parser (irssi style logs)

    @copyright: 2004 Thomas Waldmann,
                2006 Georg Brandl (support for /actions)
    @license: GNU GPL, see COPYING for details.
"""

import re

Dependencies = []

class Parser:
    """
        Send IRC logs in a table
    """
    extensions = ['.irc']
    Dependencies = []

    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request
        self.form = request.form
        self._ = request.getText
        self.out = kw.get('out', request)

    def format(self, formatter):
        fmt = formatter
        lines = self.raw.split('\n')
        # TODO: Add support for displaying things like join and part messages.
        timestamp = r"""
            ((\[|\()?                      # Opening bracket or paren for the timestamp (if it exists)
                (?P<time>                  # Timestamp
                    ((\d{1,4} [-/]?)+      # Date as one or more - or /-separated groups of digits (if it exists)
                     [T ])?                # Date/time separator: T or space
                    (\d?\d [:.]?)+         # Time as one or more :/.-separated groups of 1 or 2 digits (if it exists)
                )
            (\]|\))?\s+)?                  # Closing bracket or paren for the timestamp (if it exists) plus whitespace
        """
        std_pattern = re.compile(timestamp + r"""
            \s*<\s*?(?P<nick>.*?)\s*?>     # Nick, maybe preceeded by whitespace, which will apply only if no timestamp
            \s+                            # Space between the nick and message
            (?P<msg>.*)                    # Message
        """, re.VERBOSE | re.UNICODE)
        act_pattern = re.compile(timestamp + r"""
            \s*(?P<stars>[*]{1,3}|-!-)\s*  # Star(s)
            (?P<nick>[^\s]+)               # Nick
            \s+                            # Space
            (?P<msg>.*)                    # Message
        """, re.VERBOSE | re.UNICODE)

        tbl_style = 'vertical-align:top;'
        write = self.out.write

        def write_tbl_cell(text, code=1, add_style=''):
            write(fmt.table_cell(1, style=tbl_style+add_style))
            if code:
                write(fmt.code(1))
            write(text)
            if code:
                write(fmt.code(0))
            write(fmt.table_cell(0))

        write(fmt.table(1))
        for line in lines:
            # maybe it's a standard line
            match = std_pattern.match(line)
            if match:
                write(fmt.table_row(1))
                write_tbl_cell(fmt.text(match.group('time') or ''))
                write_tbl_cell(fmt.text(match.group('nick') or ''),
                               add_style='text-align:right; font-weight:bold')
                write_tbl_cell(fmt.text(match.group('msg') or ''), code=0)
                write(fmt.table_row(0))
            # maybe it's an ACTION
            match = act_pattern.match(line)
            if match:
                write(fmt.table_row(1))
                write_tbl_cell(fmt.text(match.group('time') or ''))
                write_tbl_cell(fmt.text(match.group('stars') or ''),
                               add_style='text-align:right')
                write_tbl_cell(fmt.emphasis(1) + fmt.code(1) + fmt.strong(1) +
                               fmt.text(match.group('nick') or '') +
                               fmt.strong(0) + fmt.code(0) +
                               fmt.text(' ' + match.group('msg')) +
                               fmt.emphasis(0), code=0)
                write(fmt.table_row(0))
        write(fmt.table(0))

