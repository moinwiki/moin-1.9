# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI apps and middlewares

    @copyright: 2003-2008 MoinMoin:ThomasWaldmann,
                2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.web.request import Request
from MoinMoin.web.contexts import XMLRPCContext

class XMLRPCApp(object):
    """ Handles XML-RPC method calls or dispatches to next layer """
    
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        request = Request(environ)
        action = Request.args.get('action')
        
        from MoinMoin import xmlrpc

        if action == 'xmlrpc':
            return xmlrpc.xmlrpc(XMLRPCContext(environ))
        elif action == 'xmlrpc2':
            return xmlrpc.xmlrpc2(XMLRPCContext(environ))
        else:
            return self.app(environ, start_response)
