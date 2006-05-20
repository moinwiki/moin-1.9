# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Utilities for writing extensions

    The stuff in this module is especially geared towards
    writing extensions / plugins, i.e. additional actions,
    macros, parsers and formatters.

    See MoinMoin.wikiutil for more.

    @copyright: 2002 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

#############################################################################
### Parameter parsing
#############################################################################

# !!! This is a lot like wikiutil.parseAttributes, and should be combined
def parseParameters(parameters, arglist):
    """ Parse a list of parameters and return a dict plus a possible
        error message.

        `parameters` is a string containing the actual arguments, while
        `arglist` is a list with tuples of the expected parameter names
        and their default value. This works identical to the call parameter
        handling of Python/C (PyArg_ParseTupleAndKeywords).

        Parameter names are case insensitive, and always returned in
        lowercase form. `arglist` is expected to contain them in lowercase
        form also.
    """
    import shlex, StringIO
    # XXX FIXME we need _ here!
    QUOTES = "\"'"
    DIGITS = "0123456789"
    parser = shlex.shlex(StringIO.StringIO(parameters))
    parser.commenters = ''
    msg = None
    pos = 0 # if this gets -1, positional params are OFF
    result = {}

    while not msg:
        key = parser.get_token()
        val = None
        if not key: break

        if pos >= 0:
            if key[0] in QUOTES:
                val = key[1:-1]
            elif key[0] in DIGITS:
                val = key
            pos += 1
        
        if val:
            # !!!!!!!!!!!!!!!!!
            pass
        else:
            eq = parser.get_token()
            if eq != "=":
                msg = _('Expected "=" to follow "%(token)s"') % {'token': key}
                break

            val = parser.get_token()
            if not val:
                msg = _('Expected a value for key "%(token)s"') % {'token': key}
                break

        """
        -----------------------------
        key = wikiutil.escape(key) # make sure nobody cheats

        # safely escape and quote value
        if val[0] in :
            val = wikiutil.escape(val)
        else:
            val = '"%s"' % wikiutil.escape(val, 1)
        """

        result[key.lower()] = val

    return result, msg or ''

