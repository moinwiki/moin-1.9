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

        result.append(formatter.div(1, css_class='footnotes'))

        # Add footnotes list
        result.append(formatter.bullet_list(1))
        for idx in range(len(request.footnotes)):
            # Add item
            result.append(formatter.listitem(1))
            result.append(formatter.paragraph(1)) # see [1]
            
            fn_id = request.footnotes[idx][1]
            result.append(formatter.anchorlink(1, 'fnref' + fn_id,
                                               id='fndef' + fn_id))
            result.append(formatter.text(str(idx + 1)))
            result.append(formatter.anchorlink(0))
            result.append(formatter.text(" "))
                        
            out=StringIO.StringIO()
            request.redirect(out)
            parser=wiki.Parser(request.footnotes[idx][0], request,
                               line_anchors=False)
            parser.format(formatter)
            result.append(out.getvalue())
            request.redirect()
            del out
            # [1] paragraph is automagically closed by wiki parser! 
            result.append(formatter.listitem(0))
            
        result.append(formatter.bullet_list(0))

        # Finish div
        result.append(formatter.div(0))

        request.footnotes = []
        return ''.join(result)

    return ''

