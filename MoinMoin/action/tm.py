# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Thread monitor action

    Shows the current traceback of all threads.

    @copyright: 2006 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.wikiutil import escape
from MoinMoin.util import thread_monitor
from StringIO import StringIO
from time import sleep

def execute(pagename, request):
    request.http_headers()

    request.theme.send_title("Thread monitor")
    request.write('<pre>')

    if not thread_monitor.hook_enabled:
        request.write("Hook is not enabled.")
    else:
        s = StringIO()
        thread_monitor.trigger_dump(s)
        sleep(5) # allow for all threads to dump to request
        request.write(escape(s.getvalue()))
        
    request.write('</pre>')
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()
