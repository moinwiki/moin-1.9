# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - FastCGI Request Implementation for fastcgi and Apache
    (and maybe others).

    @copyright: 2001-2003 by Jürgen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import sys, os
from MoinMoin import config
from MoinMoin.request import RequestBase

class Request(RequestBase):
    """ specialized on FastCGI requests """

    def __init__(self, fcgRequest, env, form, properties={}):
        """ Initializes variables from FastCGI environment and saves
            FastCGI request and form for further use.

            @param fcgRequest: the FastCGI request instance.
            @param env: environment passed by FastCGI.
            @param form: FieldStorage passed by FastCGI.
        """
        try:
            self.fcgreq = fcgRequest
            self.fcgenv = env
            self.fcgform = form
            self._setup_vars_from_std_env(env)
            RequestBase.__init__(self, properties)

        except Exception, err:
            self.fail(err)

    def _setup_args_from_cgi_form(self, form=None):
        """ Override to use FastCGI form """
        if form is None:
            form = self.fcgform
        return RequestBase._setup_args_from_cgi_form(self, form)

    def read(self, n=None):
        """ Read from input stream. """
        if n is None:
            return self.fcgreq.stdin.read()
        else:
            return self.fcgreq.stdin.read(n)

    def write(self, *data):
        """ Write to output stream. """
        self.fcgreq.out.write(self.encode(data))

    def flush(self):
        """ Flush output stream. """
        self.fcgreq.flush_out()

    def finish(self):
        """ Call finish method of FastCGI request to finish handling of this request. """
        RequestBase.finish(self)
        self.fcgreq.finish()

    # Headers ----------------------------------------------------------

    def http_headers(self, more_headers=[]):
        """ Send out HTTP headers. Possibly set a default content-type. """
        if getattr(self, 'sent_headers', None):
            return
        self.sent_headers = 1
        have_ct = 0

        # send http headers
        for header in more_headers + getattr(self, 'user_headers', []):
            if type(header) is unicode:
                header = header.encode('ascii')
            if header.lower().startswith("content-type:"):
                # don't send content-type multiple times!
                if have_ct: continue
                have_ct = 1
            self.write("%s\r\n" % header)

        if not have_ct:
            self.write("Content-type: text/html;charset=%s\r\n" % config.charset)

        self.write('\r\n')

        #from pprint import pformat
        #sys.stderr.write(pformat(more_headers))
        #sys.stderr.write(pformat(self.user_headers))

