# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Form Macro

    Displays a form definition on a page, and also processes the
    POSTed inputs.

    Usage:
        [[Form(PageDefiningTheForm)]]

    TODO:
        * Much of the code here is duplicated from Page.py (bad!)
    
    @copyright: 2002-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil, wikiform
from MoinMoin.Page import Page

Dependencies = ["time"]

def execute(macro, args):
    _ = macro.request.getText
    pagename = args

    if not wikiutil.isFormPage(macro.request, pagename):
        return (macro.formatter.sysmsg(1) +
                macro.formatter.text('Not a form page: %s' % args) +
                macro.formatter.sysmsg(0))

    formpage = Page(macro.request, pagename)
    body = formpage.get_raw_body()

    pi_formtext = []
    pi_formfields = []

    while body and body[0] == '#':
        # extract first line
        try:
            line, body = body.split('\n', 1)
        except ValueError:
            line = body
            body = ''

        # skip comments (lines with two hash marks)
        if line[1] == '#': continue

        # parse the PI
        verb, args = (line[1:]+' ').split(' ', 1)
        verb = verb.lower()
        args = args.strip()

        if verb != 'form': continue

        # collect form definitions
        if not pi_formtext:
            pi_formtext.append('<table border="1" cellspacing="1" cellpadding="3">\n'
                '<form method="POST" action="%s">\n'
                '<input type="hidden" name="action" value="formtest">\n' % 'action')
        pi_formtext.append(wikiform.parseDefinition(macro.request, args, pi_formfields))

    # user-defined form preview?
    if pi_formtext:
        pi_formtext.append('<input type="hidden" name="fieldlist" value="%s">\n' %
            "|".join(pi_formfields))
        pi_formtext.append('</form></table>\n')

    return macro.formatter.rawHTML(''.join(pi_formtext))

