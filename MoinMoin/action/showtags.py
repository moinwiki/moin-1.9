# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "showtags" action

    This action shows all sync tags related to a specific page.

    @copyright: 2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import config
from MoinMoin.Page import Page
from MoinMoin.wikisync import TagStore

def execute(pagename, request):
    mimetype = "text/plain"

    request.emit_http_headers(["Content-Type: %s; charset=%s" % (mimetype, config.charset)])

    page = Page(request, pagename)
    tags = TagStore(page)
    request.write(tags.dump())

