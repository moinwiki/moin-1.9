"""
    MoinMoin - Render as DocBook action - redirects to the DocBook formatter

    @copyright: 2005 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from MoinMoin.Page import Page

def execute(pagename, request):
    url = Page(request, pagename).url(request, {'action': 'show', 'mimetype': 'text/docbook'})
    return abort(redirect(url))

