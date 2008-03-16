# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - dump form data we received (debugging)

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import util

def execute(pagename, request):
    """ dump the form data we received in this request for debugging """
    data = util.dumpFormData(request.form)

    request.emit_http_headers()
    request.write("<html><body>%s</body></html>" % data)

