# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Load I18N Text and substitute data.

    This macro has the main purpose of being used by extensions that write
    data to wiki pages but want to ensure that it is properly translated.

    @copyright: 2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.packages import unpackLine

Dependencies = ["language"]

def execute(macro, args):
    """ args consists of a character specifiying the separator and then a
    packLine sequence describing a list. The first element of it is the message
    and the remaining elements are substituted in the message using string
    substitution.
    """
    sep = args[0]
    args = unpackLine(args[1:], sep)
    if args:
        translation = macro.request.getText(args[0])
    else:
        translation = u""
    message = translation % tuple(args[1:])

    return macro.formatter.text(message)

