# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "sitemap" action

    Generate a URL list of all your pages (using google's sitemap XML format).

    @copyright: 2006 by Thomas Waldmann, MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import config, wikiutil
from MoinMoin.util import MoinMoinNoFooter

def execute(pagename, request):
    _ = request.getText
    form = request.form

    mimetype = "text/xml"

    base = request.getBaseURL()

    request.http_headers(["Content-Type: %s; charset=%s" % (mimetype, config.charset)])

    request.write("""<?xml version="1.0" encoding="UTF-8"?>\r\n"""
                  """<urlset xmlns="http://www.google.com/schemas/sitemap/0.84">\r\n""")

    request.write("<url><loc>%s/</loc></url>\r\n" % (base,))

    # Get page dict readable by current user
    pages = request.rootpage.getPageDict()
    pagelist = pages.keys()
    pagelist.sort()

    for name in pagelist:
        url = pages[name].url(request)
        request.write("<url><loc>%s%s</loc></url>\r\n" % (base, url))

    request.write("""</urlset>\r\n""")

    raise MoinMoinNoFooter

