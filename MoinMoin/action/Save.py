# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Action macro for saving a page without processing instructions 

    MODIFICATION HISTORY:
        @copyright: 2007 by Reimar Bauer 
        @license: GNU GPL, see COPYING for details.
"""
import os
from MoinMoin.Page import Page
from MoinMoin.action import AttachFile
from MoinMoin.util import timefuncs

def execute(pagename, request):
    _ = request.getText
    thispage = Page(request, pagename)
    msg = _("You are not allowed to view this page.")
    if request.user.may.read(pagename):
        attachment_path = AttachFile.getAttachDir(request, pagename, create=1)
        timestamp = timefuncs.formathttpdate(int(os.path.getmtime(attachment_path)))
        file = "%s.txt" % pagename
        raw = Page(request, pagename).get_raw_body()
        lines = raw.split('\n')
        result = []
        for line in lines:
            is_good = True
            for pi in ("#format", "#refresh", "#redirect", "#deprecated",
                       "#pragma", "#form", "#acl", "#language"):
                if line.lower().startswith(pi):
                    is_good = False
                    break
            if is_good:
                result.append(line)
        result = '\n'.join(result)

        content_type = "text/plain"
        request.emit_http_headers([
            'Content-Type:  %s' % content_type,
            'Last-Modified: %s' % timestamp,
            'Content-Length: %d' % len(result),
            'Content-Disposition: %s; filename="%s"' % ('attachment', file),
             ])
        request.write(result)

    return thispage.send_page(request, msg=msg)

