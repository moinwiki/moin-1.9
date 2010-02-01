# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - FastCGI Request Implementation for fastcgi and Apache
    (and maybe others).

    @copyright: 2001-2003 Juergen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.request import RequestBase, RemoteClosedConnection

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

    def _setup_args_from_cgi_form(self):
        """ Override to use FastCGI form """
        # thfcgi used keep_blank_values=1 internally for fcgform
        return RequestBase._setup_args_from_cgi_form(self, self.fcgform)

    def read(self, n):
        """ Read from input stream. """
        if n is None:
            logging.warning("calling request.read(None) might block")
            return self.fcgreq.stdin.read()
        else:
            return self.fcgreq.stdin.read(n)

    def write(self, *data):
        """ Write to output stream. """
        data = self.encode(data)
        try:
            self.fcgreq.out.write(data)
        except Exception:
            raise RemoteClosedConnection()

    def send_file(self, fileobj, bufsize=8192, do_flush=True):
        # as thfcgi buffers everything we write until we do a flush, we use
        # do_flush=True as default here (otherwise the sending of big file
        # attachments would consume lots of memory)
        return RequestBase.send_file(self, fileobj, bufsize, do_flush)

    def flush(self):
        """ Flush output stream. """
        self.fcgreq.flush_out()

    def finish(self):
        """ Call finish method of FastCGI request to finish handling of this request. """
        RequestBase.finish(self)
        self.fcgreq.finish()

    def _emit_http_headers(self, headers):
        """ private method to send out preprocessed list of HTTP headers """
        for header in headers:
            self.write("%s\r\n" % header)
        self.write("\r\n")

