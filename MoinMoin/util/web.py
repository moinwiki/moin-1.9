# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Helper functions for WWW stuff

    @copyright: 2002 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re
from MoinMoin import config, wikiutil

def isSpiderAgent(request):
    """ Return True if user agent appears to be a spider.
    """
    if not request.cfg.ua_spiders:
        return 0

    ua = request.getUserAgent()
    if not ua:
        return 0

    return re.search(request.cfg.ua_spiders, ua, re.I) is not None


def parseQueryString(qstr):
    """ Parse a querystring "key=value&..." into a dict.
    """
    import cgi
    values = {}
    for key, value in cgi.parse_qs(qstr).items():
        if len(value) < 2:
            values[key] = ''.join(value)
    return values


def makeQueryString(qstr=None, **kw):
    """ Make a querystring from arguments.
        
    kw arguments overide values in qstr.

    If a string is passed in, it's returned verbatim and
    keyword parameters are ignored.

    @param qstr: dict to format as query string, using either ascii or unicode
    @param kw: same as dict when using keywords, using assci or unicode
    @rtype: string
    @return: query string ready to use in a url
    """
    if qstr is None:
        qstr = {}
    if isinstance(qstr, type({})):
        qstr.update(kw)        
        q = lambda x: wikiutil.url_quote_plus(x)
        items = ['%s=%s' % (q(key), q(value)) for key, value in qstr.items()]
        qstr = '&'.join(items)
    
    return qstr


def getIntegerInput(request, fieldname, default=None, minval=None, maxval=None):
    """ Get an integer value from a request parameter. If the value
        is out of bounds, it's made to fit into those bounds.

        Returns `default` in case of errors (not a valid integer, or field
        is missing).
    """
    try:
        result = int(request.form[fieldname][0])
    except (KeyError, ValueError):
        return default
    else:
        if minval is not None:
            result = max(result, minval)
        if maxval is not None:
            result = min(result, maxval)
        return result


def getLinkIcon(request, formatter, scheme):
    """ Get icon for fancy links, or '' if user doesn't want them.
    """
    if scheme in ["mailto", "news", "telnet", "ftp", "file"]:
        icon = scheme
    else:
        icon = "www"

    return request.theme.make_icon(icon)

def makeSelection(name, values, selectedval=None):
    """ Make a HTML <select> element named `name` from a value list.
        The list can either be a list of strings, or a list of
        (value, label) tuples.

        `selectedval` is the value that should be pre-selected.
    """
    from MoinMoin.widget import html
    result = html.SELECT(name=name)
    for val in values:
        if not isinstance(val, type(())):
            val = (val, val)
        result.append(html.OPTION(
            value=val[0], selected=(val[0] == selectedval))
            .append(html.Text(val[1]))
        )

    return result

