# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - mod_python Request Implementation for Apache and mod_python.

    @copyright: 2001-2003 Juergen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import wikiutil
from MoinMoin.request import RequestBase, RemoteClosedConnection

class Request(RequestBase):
    """ specialized on mod_python requests """

    def __init__(self, req, properties={}):
        """ Saves mod_pythons request and sets basic variables using
            the req.subprocess_env, cause this provides a standard
            way to access the values we need here.

            @param req: the mod_python request instance
        """
        try:
            # flags if headers sent out contained content-type or status
            self._have_ct = 0
            self._have_status = 0

            req.add_common_vars()
            self.mpyreq = req
            # some mod_python 2.7.X has no get method for table objects,
            # so we make a real dict out of it first.
            if not hasattr(req.subprocess_env, 'get'):
                env = dict(req.subprocess_env)
            else:
                env = req.subprocess_env
            self._setup_vars_from_std_env(env)
            RequestBase.__init__(self, properties)

        except Exception, err:
            self.fail(err)

    def fixURI(self, env):
        """ Fix problems with script_name and path_info using
        PythonOption directive to rewrite URI.

        This is needed when using Apache 1 or other server which does
        not support adding custom headers per request. With mod_python we
        can use the PythonOption directive:

            <Location /url/to/mywiki/>
                PythonOption X-Moin-Location /url/to/mywiki/
            </location>

        Note that *neither* script_name *nor* path_info can be trusted
        when Moin is invoked as a mod_python handler with apache1, so we
        must build both using request_uri and the provided PythonOption.
        """
        # Be compatible with release 1.3.5 "Location" option
        # TODO: Remove in later release, we should have one option only.
        old_location = 'Location'
        options_table = self.mpyreq.get_options()
        if not hasattr(options_table, 'get'):
            options = dict(options_table)
        else:
            options = options_table
        location = options.get(self.moin_location) or options.get(old_location)
        if location:
            env[self.moin_location] = location
            # Try to recreate script_name and path_info from request_uri.
            import urlparse
            scriptAndPath = urlparse.urlparse(self.request_uri)[2]
            self.script_name = location.rstrip('/')
            path = scriptAndPath.replace(self.script_name, '', 1)
            self.path_info = wikiutil.url_unquote(path, want_unicode=False)

        RequestBase.fixURI(self, env)

    def _setup_args_from_cgi_form(self):
        """ Override to use mod_python.util.FieldStorage

        It's little different from cgi.FieldStorage, so we need to
        duplicate the conversion code.
        """
        from mod_python import util
        form = util.FieldStorage(self.mpyreq, keep_blank_values=1) # by default this evaluates query string AND body POST data!

        args = {}

        # You cannot get rid of .keys() here
        for key in form.keys():
            if key is None:
                continue
            values = form[key]
            if not isinstance(values, list):
                values = [values]
            fixedResult = []
            for item in values:
                if isinstance(item, util.StringField):
                    fixedResult.append(item.value)
                elif isinstance(item, util.Field) and item.filename:
                    fixedResult.append(item.file)
                    # Remember filenames with a name hack
                    args[key + '__filename__'] = item.filename
                    # XXX Now it gets extremely dirty to work around a problem in mod_python 3.3.1: XXX
                    # Without the next line, item.file will be closed when item/form leaves this scope.
                    # I guess some reference counting is not implemented correctly for item.file,
                    # so we just keep a reference to item to keep it alive...
                    fixedResult.append(item)  # we are lucky, nobody uses the 2nd list item anyway
                    # If you are reading this, please switch to mod_wsgi. :)
                elif isinstance(item, str):
                    # mod_python 2.7 might return strings instead of Field objects.
                    fixedResult.append(item)
            args[key] = fixedResult

        result = self.decodeArgs(args)
        return result  # XXX without the hack above, item.file gets closed when returning! XXX

    def run(self, req):
        """ mod_python calls this with its request object. We don't
            need it cause its already passed to __init__. So ignore
            it and just return RequestBase.run.

            @param req: the mod_python request instance
        """
        return RequestBase.run(self)

    def read(self, n):
        """ Read from input stream. """
        if n is None:
            logging.warning("calling request.read(None) might block")
            return self.mpyreq.read()
        else:
            return self.mpyreq.read(n)

    def write(self, *data):
        """ Write to output stream. """
        data = self.encode(data)
        try:
            self.mpyreq.write(data)
        except Exception:
            raise RemoteClosedConnection()

    def flush(self):
        """ We can't flush it, so do nothing. """
        pass

    def finish(self):
        """ Just return apache.OK. Status is set in req.status. """
        RequestBase.finish(self)
        # is it possible that we need to return something else here?
        from mod_python import apache
        return apache.OK

    def _emit_http_headers(self, headers):
        """ private method to send out preprocessed list of HTTP headers """
        st_header, ct_header, other_headers = headers[0], headers[1], headers[2:]
        status = st_header.split(':', 1)[1].lstrip()
        self.mpyreq.status = int(status.split(' ', 1)[0])
        self.mpyreq.content_type = ct_header.split(':', 1)[1].lstrip()
        for header in other_headers:
            key, value = header.split(':', 1)
            value = value.lstrip()
            self.mpyreq.headers_out[key] = value
        # this is for mod_python 2.7.X, for 3.X it's a NOP
        self.mpyreq.send_http_header()

