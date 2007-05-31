# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber notification plugin from event system

    This code sends notifications using a separate daemon.

@copyright: 2007 by Karol Nowak <grywacz@gmail.com>
@license: GNU GPL, see COPYING for details.
"""

import xmlrpclib
from MoinMoin.events import PageEvent, PageChangedEvent

server = None

def handle(event):
    global server
    
    if not isinstance(event, PageEvent) or event.request.cfg.bot_host is None:
        return
    
    # Create an XML RPC server object only if it doesn't exist
    if server is None:
        server = xmlrpclib.Server("http://" + event.request.cfg.bot_host)
    
    msg = u"Page %(page_name)s has been modified!\n" % ( {'page_name': event.page.page_name} )
    
    if event.comment:
        msg = msg + u"The comment is: %(comment)s\n" % ( {'comment': event.comment} )
    
    if event.trivial:
        msg = msg + u"This change has been marked as TRIVIAL.\n"
        
    try:
        server.send_notification(u"grzyw@jabber.org", msg)
    except Exception, desc:
        print "XML RPC error:", desc
