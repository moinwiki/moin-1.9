# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - FootNote Macro

    Collect and emit footnotes. Note that currently footnote
    text cannot contain wiki markup.

    @copyright: 2002 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import sha, StringIO
from MoinMoin import config
from MoinMoin.parser import wiki

Dependencies = ["time"] # footnote macro cannot be cached

def execute(macro, args):
    # create storage for footnotes
    if not hasattr(macro.request, 'footnotes'):
        macro.request.footnotes = []
    
    if not args:
        return emit_footnotes(macro.request, macro.formatter)
    else:
        # store footnote and emit number
        idx = len(macro.request.footnotes)
        fn_id = "-%s-%s" % (sha.new(args.encode(config.charset)).hexdigest(), idx)
        macro.request.footnotes.append((args, fn_id))
        return "%s%s%s%s%s" % (
            macro.formatter.sup(1),
            macro.formatter.anchorlink(1, 'fndef' + fn_id, id = 'fnref' + fn_id),
            macro.formatter.text(str(idx+1)),
            macro.formatter.anchorlink(0),
            macro.formatter.sup(0),)

    # nothing to do or emit
    return ''


def emit_footnotes(request, formatter):
    # emit collected footnotes
    if request.footnotes:
        result = []

        # Start footnotes div. It is important to use formatter so open
        # inline tags will be closed, and we get correct direction.
        attr = formatter.langAttr()
        attr['class'] = 'footnotes'
        result.append(formatter.open('div', attr=attr))

        # What is that empty div for???
        result.append('<div></div>\n')

        # Add footnotes list
        result.append('<ul>\n')
        for idx in range(len(request.footnotes)):
            # Add item
            fn_id = request.footnotes[idx][1]
            fn_no = (formatter.anchorlink(1, 'fnref' + fn_id, id = 'fndef' + fn_id) +
                     formatter.text(str(idx+1)) +
                     formatter.anchorlink(0))

            result.append('<li><span>%s</span>' % fn_no)
                        
            out=StringIO.StringIO()
            request.redirect(out)
            parser=wiki.Parser(request.footnotes[idx][0], request)
            parser.format(formatter)
            result.append(out.getvalue())
            request.redirect()
            del out
            
            result.append('</li>\n')
            
        result.append('</ul>\n')

        # Finish div
        result.append(formatter.close('div'))

        request.footnotes = []
        return ''.join(result)

    return ''

