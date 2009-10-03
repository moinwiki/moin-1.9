# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Twisted Request Implementation

    @copyright: 2001-2003 Juergen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.request import RequestBase, MoinMoinFinish, RemoteClosedConnection

class Request(RequestBase):
    """ specialized on Twisted requests """

    def __init__(self, twistedRequest, pagename, reactor, properties={}):
        try:
            self.twistd = twistedRequest
            self.reactor = reactor

            # Copy headers
            self.http_accept_language = self.twistd.getHeader('Accept-Language')
            self.saved_cookie = self.twistd.getHeader('Cookie')
            self.http_user_agent = self.twistd.getHeader('User-Agent')
            try:
                self.content_length = int(self.twistd.getHeader('Content-Length'))
            except (TypeError, ValueError):
                self.content_length = None
            self.if_modified_since = self.twistd.getHeader('If-Modified-Since')
            self.if_none_match = self.twistd.getHeader('If-None-Match')

            # Copy values from twisted request
            self.server_protocol = self.twistd.clientproto
            self.server_name = self.twistd.getRequestHostname().split(':')[0]
            self.server_port = str(self.twistd.getHost()[2])
            self.is_ssl = self.twistd.isSecure()
            self.path_info = '/' + '/'.join([pagename] + self.twistd.postpath)
            self.request_method = self.twistd.method
            self.remote_addr = self.twistd.getClientIP()
            self.request_uri = self.twistd.uri
            self.script_name = "/" + '/'.join(self.twistd.prepath[:-1])

            # Values that need more work
            self.query_string = self.splitURI(self.twistd.uri)[1]
            self.setHttpReferer(self.twistd.getHeader('Referer'))
            self.setHost()
            self.setURL(self.twistd.getAllHeaders())

            ##self.debugEnvironment(twistedRequest.getAllHeaders())

            RequestBase.__init__(self, properties)

        except MoinMoinFinish: # might be triggered by http_redirect
            self.emit_http_headers() # send headers (important for sending MOIN_ID cookie)
            self.finish()

        except Exception, err:
            # Wrap err inside an internal error if needed
            from MoinMoin import error
            if isinstance(err, error.FatalError):
                self.delayedError = err
            else:
                self.delayedError = error.InternalError(str(err))

    def run(self):
        """ Handle delayed errors then invoke base class run """
        if hasattr(self, 'delayedError'):
            self.fail(self.delayedError)
            return self.finish()
        RequestBase.run(self)

    def setup_args(self):
        """ Return args dict

        Twisted already parsed args, including __filename__ hacking,
        but did not decode the values.
        """
        # All of the arguments, including URL and POST arguments (using keep_blank_values=1 internally).
        return self.decodeArgs(self.twistd.args)

    def read(self, n):
        """ Read from input stream. """
        # XXX why is that wrong?:
        #rd = self.reactor.callFromThread(self.twistd.read)

        # XXX do we need self.reactor.callFromThread with that?
        # XXX if yes, why doesn't it work?
        self.twistd.content.seek(0, 0)
        if n is None:
            logging.warning("calling request.read(None) might block")
            rd = self.twistd.content.read()
        else:
            rd = self.twistd.content.read(n)
        #print "request.RequestTwisted.read: data=\n" + str(rd)
        return rd

    def write(self, *data):
        """ Write to output stream. """
        #print "request.RequestTwisted.write: data=\n" + wd
        data = self.encode(data)
        try:
            self.reactor.callFromThread(self.twistd.write, data)
        except Exception:
            raise RemoteClosedConnection()

    def flush(self):
        pass # XXX is there a flush in twisted?

    def finish(self):
        RequestBase.finish(self)
        self.reactor.callFromThread(self.twistd.finish)

    # Headers ----------------------------------------------------------

    def _emit_http_headers(self, headers):
        """ private method to send out preprocessed list of HTTP headers """
        st_header, other_headers = headers[0], headers[1:]
        status = st_header.split(':', 1)[1].lstrip()
        status_code, status_msg = status.split(' ', 1)
        self.twistd.setResponseCode(int(status_code), status_msg)
        for header in other_headers:
            key, value = header.split(':', 1)
            value = value.lstrip()
            if key.lower() == 'set-cookie':
                key, value = value.split('=', 1)
                self.twistd.addCookie(key, value)
            else:
                self.twistd.setHeader(key, value)

    def http_redirect(self, url, code=302):
        """ Redirect to a fully qualified, or server-rooted URL

        TODO: use code 301 or 302 to generate correct header

        @param url: relative or absolute url, ascii using url encoding.
        """
        url = self.getQualifiedURL(url)
        self.twistd.redirect(url)
        # calling finish here will send the rest of the data to the next
        # request. leave the finish call to run()
        #self.twistd.finish()
        raise MoinMoinFinish

