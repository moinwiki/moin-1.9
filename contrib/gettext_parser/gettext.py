# -*- coding: iso-8859-15 -*-
"""
    MoinMoin - GetText .po parser for moin 1.3.x

    Usage:
    ======

    Either begin your page like this:
    #format gettext
    (followed by .po file content only)

    Or attach the .po file and inline it:
    ... (wiki markup) ...
    inline:de.po
    ... (wiki markup) ...

    Of course, if you just attach the file, you won't be able to edit it in
    the wiki. So the #format method is better for online editing.

    Requirements:
    =============

    * requires Python 2.4 and installed "gettext" package (msgfmt)
    * requires wiki page content to be in config.charset, so do not put non-
      utf-8 content into a utf-8 wiki or it will crash.

    @copyright: 2005 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

Dependencies = []

import subprocess
from MoinMoin import config

class Parser:
    extensions = ['.po']

    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request

    def format(self, formatter):
        PIPE = subprocess.PIPE
        STDOUT = subprocess.STDOUT
        p = subprocess.Popen(("msgfmt", "-c", "--statistics", "-", ), shell=False,
                             stdin=PIPE, stdout=PIPE, stderr=STDOUT)

        charset = config.charset
        textin = self.raw.encode(charset)
        out = p.communicate(input=textin)[0]
        if out is None:
            out = ''
        out = out.decode(charset).replace('<stdin>:', 'input data line ')

        # show po file data with line numbers as msgfmt refers to them
        text, lineno = [], 0
        for l in self.raw.splitlines():
            lineno += 1
            text.append("%04d: %s" % (lineno, l))

        textout = [formatter.heading(1, 3),
                   'Gettext status messages:',
                   formatter.heading(0, 3),
                   formatter.preformatted(1),
                   formatter.text(out),
                   formatter.preformatted(0),
                   formatter.heading(1, 3),
                   'Input:',
                   formatter.heading(0, 3),
                   formatter.preformatted(1),
                   formatter.text("\n".join(text)),
                   formatter.preformatted(0),
                  ]

        self.request.write(''.join(textout))

