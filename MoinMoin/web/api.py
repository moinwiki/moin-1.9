# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Interface definitions

    Interface definitions for the Request object and associated classes
    and services.

    @copyright: 2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

class Interface(object):
    """ An interface (marker class) """

class IContext(Interface):
    """
    A context object represents the request in different phases of the
    request/response cycle, e.g. session setup, page renderin (formatter
    or parser), XML-RPC, etc.
    """
    def become(cls):
        """ Become another context, based on the given class. """


class ISessionService(Interface):
    """
    A session service returns a session object given a request object and
    provides services like persisting sessions and cleaning up occasionally.
    """
    def get_session(request):
        """ Return a session object pertaining to the particular request."""

    def finalize(request, session):
        """
        Do final modifications to the request and/or session before sending
        headers and body to the cliebt.
        """
        
