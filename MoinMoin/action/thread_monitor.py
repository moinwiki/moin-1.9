# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Thread monitor action

    Shows the current traceback of all threads.

    @copyright: 2006 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""
import os, time
from StringIO import StringIO
 
from MoinMoin import wikiutil
from MoinMoin.util import thread_monitor
 
def execute_fs(pagename, request):
    if thread_monitor.hook_enabled:
        s = StringIO()
        thread_monitor.trigger_dump(s)
        time.sleep(5) # allow for all threads to dump to request
        data = s.getvalue()
        timestamp = time.time()
        dump_fname = os.path.join(request.cfg.data_dir, "tm_%d.log" % timestamp)
        f = file(dump_fname, "w")
        f.write(data)
        f.close()
    else:
        dump_fname = "nowhere"

    request.http_headers()
    request.write('<html><body>A dump has been saved to %s.</body></html>' % dump_fname)

def execute_wiki(pagename, request):
    request.http_headers()

    request.theme.send_title("Thread monitor")
    request.write('<pre>')

    if not thread_monitor.hook_enabled:
        request.write("Hook is not enabled.")
    else:
        s = StringIO()
        thread_monitor.trigger_dump(s)
        time.sleep(5) # allow for all threads to dump to request
        request.write(wikiutil.escape(s.getvalue()))
        
    request.write('</pre>')
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()
  
execute = execute_fs

