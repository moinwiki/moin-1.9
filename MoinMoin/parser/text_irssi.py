# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - IRC Log Parser (irssi style logs)

    @copyright: 2004 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import re
from MoinMoin import wikiutil

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
        lines = self.raw.split('\n')
        # TODO: Add support for displaying things like join and part messages.
        pattern = re.compile(r"""
            ((\[|\()?                      # Opening bracket or paren for the timestamp (if it exists)
                (?P<time>([\d]?\d[:.]?)+)  # Timestamp as one or more :/.-separated groups of 1 or 2 digits (if it exists)
            (\]|\))?\s+)?                  # Closing bracket or paren for the timestamp (if it exists) plus whitespace
            \s*<\s*?(?P<nick>.*?)\s*?>     # Nick, maybe preceeded by whitespace, which will apply only if no timestamp
            \s+                            # Space between the nick and message
            (?P<msg>.*)                    # Message
        """, re.VERBOSE + re.UNICODE)
        self.out.write(formatter.table(1))
        for line in lines:
            match = pattern.match(line)
            if match:
                self.out.write(formatter.table_row(1))
                for g in ('time', 'nick', 'msg'):
                    self.out.write(formatter.table_cell(1))
                    self.out.write(formatter.text(match.group(g) or ''))
                    self.out.write(formatter.table_cell(0))
                self.out.write(formatter.table_row(0))
        self.out.write(formatter.table(0))

