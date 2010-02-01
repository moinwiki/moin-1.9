# -*- coding: iso-8859-1 -*-
"""
    MoinMoin.server.server_twisted

    Create standalone twisted based server.

    Minimal usage:

        from MoinMoin.server.server_twisted import TwistedConfig, makeApp

        class Config(TwistedConfig):
            docs = '/usr/share/moin/wiki/htdocs'
            user = 'www-data'
            group = 'www-data'

        application = makeApp(Config)

    Then run this code with twistd -y yourcode.py. See moin_twisted script.

    @copyright: 2004 Thomas Waldmann, Oliver Graf, Nir Soffer
    @license: GNU GPL, see COPYING for details.
"""

from twisted.application import internet, service
from twisted.web import static, server, vhost, resource
from twisted.internet import threads, reactor

try:
    from twisted.internet import ssl
except ImportError:
    ssl = None

# Enable threads
from twisted.python import threadable
threadable.init(1)

# MoinMoin imports
from MoinMoin.request import request_twisted
from MoinMoin.server import Config

# Set threads flag, so other code can use proper locking
from MoinMoin import config
config.use_threads = True
del config

# Server globals
config = None


class WikiResource(resource.Resource):
    """ Wiki resource """
    isLeaf = 1

    def render(self, request):
        return server.NOT_DONE_YET


class WikiRoot(resource.Resource):
    """ Wiki root resource """

    def getChild(self, name, request):
        # Serve images and css from url_prefix_static
        if request.prepath == [] and name == config.url_prefix_static[1:]:
            return resource.Resource.getChild(self, name, request)

        # Serve special 'root' files from url_prefix_static
        elif name in ['favicon.ico', 'robots.txt'] and request.postpath == []:
            return self.children[config.url_prefix_static[1:]].getChild(name, request)

        # All other through moin

        # TODO: fix profile code to include the request init and ignore
        # first request. I'm not doing this now since its better done
        # with the new twisted code waiting in fix branch. --Nir
        else:
            if config.memoryProfile:
                config.memoryProfile.addRequest()
            req = request_twisted.Request(request, name, reactor, properties=config.properties)
            if config.hotshotProfile:
                threads.deferToThread(config.hotshotProfile.runcall, req.run)
            else:
                threads.deferToThread(req.run)
            return WikiResource()


class MoinRequest(server.Request):
    """ MoinMoin request

    Enable passing of file-upload filenames
    """

    def requestReceived(self, command, path, version):
        """ Called by channel when all data has been received.

        Override server.Request method for POST requests, to fix file
        uploads issue.
        """
        if command == 'POST':
            self.requestReceivedPOST(path, version)
        else:
            server.Request.requestReceived(self, command, path, version)

    def requestReceivedPOST(self, path, version):
        """ Handle POST requests

        This is a modified copy of server.Request.requestRecived,
        modified to use cgi.FieldStorage to handle file uploads
        correctly.

        Creates an extra member extended_args which also has
        filenames of file uploads ( FIELDNAME__filename__ ).
        """
        import cgi

        self.content.seek(0, 0)
        self.args = {}
        self.extended_args = {}
        self.stack = []

        self.method = 'POST'
        self.uri = path
        self.clientproto = version
        x = self.uri.split('?')

        argstring = ""
        if len(x) == 1:
            self.path = self.uri
        else:
            if len(x) != 2:
                from twisted.python import log
                log.msg("May ignore parts of this invalid URI: %s"
                        % repr(self.uri))
            self.path, argstring = x[0], x[1]

        # cache the client and server information, we'll need this later to be
        # serialized and sent with the request so CGIs will work remotely
        self.client = self.channel.transport.getPeer()
        self.host = self.channel.transport.getHost()

        # create dummy env for cgi.FieldStorage
        env = {
            'REQUEST_METHOD': self.method,
            'QUERY_STRING': argstring,
            }
        form = cgi.FieldStorage(fp=self.content,
                                environ=env,
                                headers=self.received_headers)

        # Argument processing

        args = self.args
        try:
            keys = form.keys()
        except TypeError:
            pass
        else:
            for key in keys:
                values = form[key]
                if not isinstance(values, list):
                    values = [values]
                fixedResult = []
                for i in values:
                    if isinstance(i, cgi.FieldStorage) and i.filename:
                        fixedResult.append(i.file)
                        # multiple uploads to same form field are stupid!
                        args[key + '__filename__'] = i.filename
                    else:
                        fixedResult.append(i.value)
                args[key] = fixedResult

        self.process()


class MoinSite(server.Site):
    """ Moin site """
    requestFactory = MoinRequest

    def startFactory(self):
        """ Setup before starting """
        # Memory profile
        if config.memoryProfile:
            config.memoryProfile.sample()

        # hotshot profile
        if config.hotshotProfile:
            import hotshot
            config.hotshotProfile = hotshot.Profile(config.hotshotProfile)
        server.Site.startFactory(self)

    def stopFactory(self):
        """ Cleaup before stoping """
        server.Site.stopFactory(self)
        if config.hotshotProfile:
            config.hotshotProfile.close()


class TwistedConfig(Config):
    """ Twisted server default config """

    name = 'mointwisted'
    properties = {}
    docs = '/usr/share/moin/htdocs'
    user = 'www-data'
    group = 'www-data'
    port = 8080
    interfaces = ['']
    threads = 10
    timeout = 15 * 60 # 15 minutes
    logPath_twisted = None # Twisted log file
    virtualHosts = None
    memoryProfile = None
    hotshotProfile = None

    # sslcert = ('/whereever/cert/sitekey.pem', '/whereever/cert/sitecert.pem')
    sslcert = None

    def __init__(self):
        Config.__init__(self)

        # Check for '' in interfaces, then ignore other
        if '' in self.interfaces:
            self.interfaces = ['']


def makeApp(ConfigClass):
    """ Generate and return an application

    See MoinMoin.server.Config for config options

    @param ConfigClass: config class
    @rtype: application object
    @return twisted application, needed by twistd
    """
    # Create config instance (raise RuntimeError if config invalid)
    global config
    config = ConfigClass()

    # Set number of threads
    reactor.suggestThreadPoolSize(config.threads)

    # The root of the HTTP hierarchy
    default = WikiRoot()

    # Here is where img and css and some special files come from
    default.putChild(config.url_prefix_static[1:], static.File(config.docs))

    # Generate the Site factory
    # TODO: Maybe we can use WikiRoot instead of this
    # ----------------------------------------------
    root = vhost.NameVirtualHost()
    root.default = default
    # ----------------------------------------------
    site = MoinSite(root, logPath=config.logPath_twisted, timeout=config.timeout)

    # Make application
    application = service.Application("web", uid=config.uid, gid=config.gid)
    sc = service.IServiceCollection(application)

    # Listen to all interfaces in config.interfaces
    for entry in config.interfaces:
        # Add a TCPServer for each interface.

        # This is an hidden experimantal feature: each entry in
        # interface may contain a port, using 'ip:port'.
        # Note: the format is subject to change!
        try:
            interface, port = entry.split(':', 1)
        except ValueError:
            interface, port = entry, config.port

        # Might raise ValueError if not integer.
        # TODO: check if we can use string port, like 'http'
        port = int(port)

        if port == 443 and ssl and ssl.supported and config.sslcert:
            sslContext = ssl.DefaultOpenSSLContextFactory(*config.sslcert)
            s = internet.SSLServer(port, site, sslContext, interface=interface)
        else:
            s = internet.TCPServer(port, site, interface=interface)
        s.setServiceParent(sc)

    return application

