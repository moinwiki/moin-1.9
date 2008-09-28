# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Stand-alone HTTP Server

    This is a simple, fast and very easy to install server. Its
    recommended for personal wikis or public wikis with little load.

    It is not well tested in public wikis with heavy load. In these case
    you might want to use twisted, fast cgi or mod python, or if you
    can't use those, cgi.

    Minimal usage:

        from MoinMoin.server.server_standalone import StandaloneConfig, run

        class Config(StandaloneConfig):
            docs = '/usr/share/moin/wiki/htdocs'
            user = 'www-data'
            group = 'www-data'

        run(Config)

    See more options in StandaloneConfig class.

    For security, the server will not run as root. If you try to run it
    as root, it will run as the user and group in the config. If you run
    it as a normal user, it will run with your regular user and group.

    Significant contributions to this module by R. Church <rc@ghostbitch.org>

    @copyright: 2001-2004 MoinMoin:JuergenHermann,
                2005 MoinMoin:AlexanderSchremmer,
                2005 MoinMoin:NirSoffer
    @license: GNU GPL, see COPYING for details.
"""

import os, sys, time, socket, errno, shutil
import BaseHTTPServer, SimpleHTTPServer, SocketServer

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import version, wikiutil
from MoinMoin.server import Config, switchUID
from MoinMoin.request import request_standalone
from MoinMoin.util import timefuncs

# Server globals
httpd = None
config = None


class SimpleServer(BaseHTTPServer.HTTPServer):
    """ Simplest server, serving one request after another

    This server is good for personal wiki, or when lowest memory
    footprint is needed.
    """
    use_threads = False

    def __init__(self, config):
        self.htdocs = config.docs
        self.request_queue_size = config.requestQueueSize
        self._abort = 0
        address = (config.interface, config.port)
        BaseHTTPServer.HTTPServer.__init__(self, address, MoinRequestHandler)

    def server_activate(self):
        BaseHTTPServer.HTTPServer.server_activate(self)
        logging.info("%s serving on %s:%d" % (self.__class__.__name__,
                                              self.server_address[0],
                                              self.server_address[1]))

    def serve_forever(self):
        """Handle one request at a time until we die """
        while not self._abort:
            self.handle_request()

    def die(self):
        """Abort this server instance's serving loop """
        # Close hotshot profiler
        if config.hotshotProfile:
            config.hotshotProfile.close()

        if config.cProfileProfile and config.cProfile:
            config.cProfile.dump_stats(config.cProfileProfile)

        # Set abort flag, then make request to wake the server
        self._abort = 1
        try:
            import httplib
            addr = self.server_address
            if not addr[0]:
                addr = ("localhost", addr[1])
            req = httplib.HTTP('%s:%d' % addr)
            req.connect()
            req.putrequest('DIE', '/')
            req.endheaders()
            del req
        except socket.error, err:
            # Ignore certain errors
            if err.args[0] not in [errno.EADDRNOTAVAIL, ]:
                raise


class ThreadingServer(SimpleServer):
    """ Serve each request in a new thread

    This server is used since release 1.3 and seems to work nice with
    little load.

    From release 1.3.5 there is a thread limit, that should help to
    limit the load on the server.
    """
    use_threads = True

    def __init__(self, config):
        self.thread_limit = config.threadLimit
        from threading import Condition
        self.lock = Condition()
        SimpleServer.__init__(self, config)

    def process_request(self, request, client_address):
        """ Start a new thread to process the request

        If the thread limit has been reached, wait on the lock. The
        next thread will notify when finished.
        """
        from threading import Thread, activeCount
        self.lock.acquire()
        try:
            if activeCount() > self.thread_limit:
                self.lock.wait()
            if self._abort:
                return
            t = Thread(target=self.process_request_thread,
                       args=(request, client_address))
            t.setDaemon(True)
            t.start()
        finally:
            self.lock.release()

    def process_request_thread(self, request, client_address):
        """ Called for each request on a new thread

        Notify the main thread on the end of each request.
        """
        try:
            self.finish_request(request, client_address)
        except:
            self.handle_error(request, client_address)
        self.close_request(request)
        self.lock.acquire()
        try:
            # Main thread might be waiting
            self.lock.notify()
        finally:
            self.lock.release()


class ThreadPoolServer(SimpleServer):
    """ Threading server using a pool of threads

    This is a new experimental server, using a pool of threads instead
    of creating new thread for each request. This is similar to Apache
    worker mpm, with a simpler constant thread pool.

    This server is 5 times faster than ThreadingServer for static
    files, and about the same for wiki pages.
    """
    use_threads = True

    def __init__(self, config):
        self.queue = []
        # The size of the queue need more testing
        self.queueSize = config.threadLimit * 2
        self.poolSize = config.threadLimit
        from threading import Condition
        self.lock = Condition()
        SimpleServer.__init__(self, config)

    def serve_forever(self):
        """ Create a thread pool then invoke base class method """
        from threading import Thread
        for dummy in range(self.poolSize):
            t = Thread(target=self.serve_forever_thread)
            t.setDaemon(True)
            t.start()
        SimpleServer.serve_forever(self)

    def process_request(self, request, client_address):
        """ Called for each request

        Insert the request into the queue. If the queue is full, wait
        until one of the request threads pop a request. During the wait,
        new connections might be dropped.
        """
        self.lock.acquire()
        try:
            if len(self.queue) >= self.queueSize:
                self.lock.wait()
            if self._abort:
                return
            self.queue.insert(0, (request, client_address))
            self.lock.notify()
        finally:
            self.lock.release()

    def serve_forever_thread(self):
        """ The main loop of request threads

        Pop a request from the queue and process it.
        """
        while not self._abort:
            request, client_address = self.pop_request()
            try:
                self.finish_request(request, client_address)
            except:
                self.handle_error(request, client_address)
            self.close_request(request)

    def pop_request(self):
        """ Pop a request from the queue

        If the queue is empty, wait for notification. If the queue was
        full, notify the main thread which may be waiting.
        """
        self.lock.acquire()
        try:
            while not self._abort:
                try:
                    item = self.queue.pop()
                    if len(self.queue) == self.queueSize - 1:
                        # Queue was full - main thread might be waiting
                        self.lock.notify()
                    return item
                except IndexError:
                    self.lock.wait()
        finally:
            self.lock.release()
        sys.exit()

    def die(self):
        """ Wake all threads then invoke base class die

        Threads should exist when _abort is True.
        """
        self._abort = True
        self.wake_all_threads()
        time.sleep(0.1)
        SimpleServer.die(self)

    def wake_all_threads(self):
        self.lock.acquire()
        try:
            self.lock.notifyAll()
        finally:
            self.lock.release()


class ForkingServer(SocketServer.ForkingMixIn, SimpleServer):
    """ Serve each request in a new process

    This is new untested server, first tests show rather pathetic cgi
    like performance. No data is cached between requests.

    The mixin has its own process limit.
    """
    max_children = 10


class MoinRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    bufferSize = 8 * 1024 # used to serve static files
    staticExpire = 365 * 24 * 3600 # 1 year expiry for static files

    def __init__(self, request, client_address, server):
        self.server_version = "MoinMoin %s %s %s" % (version.release,
                                                     version.revision,
                                                     server.__class__.__name__)
        self.expires = 0
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, request,
            client_address, server)

    def log_message(self, format, *args):
        logging.info("%s %s" % (self.address_string(), format % args))

    # -------------------------------------------------------------------
    # do_METHOD dispatchers - called for each request

    def do_DIE(self):
        if self.server._abort:
            self.log_error("Shutting down")

    def do_ALL(self):
        """ Handle requests (request type GET/HEAD/POST is in self.command)

        Separate between wiki pages and css and image url by similar
        system as cgi and twisted, the url_prefix_static prefix.
        """
        prefix = config.url_prefix_static
        if self.path.startswith(prefix + '/'):
            self.path = self.path[len(prefix):]
            self.serve_static_file()
        elif self.path in ['/favicon.ico', '/robots.txt']:
            self.serve_static_file()
        else:
            self.serve_moin()

    do_POST = do_ALL
    do_GET = do_ALL
    do_HEAD = do_ALL

    # -------------------------------------------------------------------
    # Serve methods

    def serve_static_file(self):
        """ Serve files from the htdocs directory """
        self.expires = self.staticExpire
        path = self.path.split("?", 1)
        if len(path) > 1:
            self.path = path[0] # XXX ?params

        try:
            fn = getattr(SimpleHTTPServer.SimpleHTTPRequestHandler, 'do_' + self.command)
            fn(self)
        except socket.error, err:
            # Ignore certain errors
            if err.args[0] not in [errno.EPIPE, errno.ECONNABORTED]:
                raise

    def serve_moin(self):
        """ Serve a request using moin """
        # don't make an Expires header for wiki pages
        self.expires = 0

        try:
            req = request_standalone.Request(self, properties=config.properties)
            req.run()
        except socket.error, err:
            # Ignore certain errors
            if err.args[0] not in [errno.EPIPE, errno.ECONNABORTED]:
                raise

    def translate_path(self, uri):
        """ Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.
        """
        path = wikiutil.url_unquote(uri, want_unicode=False)
        path = path.replace('\\', '/')
        words = path.split('/')
        words = filter(None, words)

        path = self.server.htdocs
        bad_uri = 0
        for word in words:
            drive, word = os.path.splitdrive(word)
            if drive:
                bad_uri = 1
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                bad_uri = 1
                continue
            path = os.path.join(path, word)

        if bad_uri:
            self.log_error("Detected bad request URI '%s', translated to '%s'"
                           % (uri, path, ))
        return path

    def end_headers(self):
        """overload the default end_headers, inserting expires header"""
        if self.expires:
            now = time.time()
            expires = now + self.expires
            self.send_header('Expires', timefuncs.formathttpdate(expires))
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        Modify the base class method to change the buffer size. Test
        shows that for the typical static files we serve, 8K buffer is
        faster than the default 16K buffer.
        """
        shutil.copyfileobj(source, outputfile, length=self.bufferSize)

    def address_string(self):
        """We don't want to do reverse DNS lookups, just return IP address."""
        return self.client_address[0]


try:
    from tlslite.api import TLSSocketServerMixIn, X509, X509CertChain, SessionCache, parsePEMKey
    from tlslite.TLSConnection import TLSConnection
except ImportError:
    pass
else:
    class SecureRequestRedirect(BaseHTTPServer.BaseHTTPRequestHandler):
        def handle(self):
            self.close_connection = 1
            try:
                self.raw_requestline = self.rfile.readline()
            except socket.error:
                return
            if self.parse_request():
                host = self.headers.get('Host', socket.gethostname())
                path = self.path
            else:
                host = '%s:%s' % (socket.gethostname(),
                        self.request.getsockname()[1])
                path = '/'

            self.requestline = 'ERROR: Redirecting to https://%s%s' % (host, path)
            self.request_version = 'HTTP/1.1'
            self.command = 'GET'
            self.send_response(301, 'Document Moved')
            self.send_header('Date', self.date_time_string())
            self.send_header('Location', 'https://%s%s' % (host, path))
            self.send_header('Connection', 'close')
            self.send_header('Content-Length', '0')
            self.wfile.write('\r\n')

    class SecureThreadPoolServer(TLSSocketServerMixIn, ThreadPoolServer):
        def __init__(self, config):
            ThreadPoolServer.__init__(self, config)

            cert = open(config.ssl_certificate).read()
            x509 = X509()
            x509.parse(cert)
            self.certChain = X509CertChain([x509])

            priv = open(config.ssl_privkey).read()
            self.privateKey = parsePEMKey(priv, private=True)

            self.sessionCache = SessionCache()

        def finish_request(self, sock, client_address):
            # Peek into the packet, if it starts with GET or POS(T) then
            # redirect, otherwise let TLSLite handle the connection.
            peek = sock.recv(3, socket.MSG_PEEK).lower()
            if peek == 'get' or peek == 'pos':
                SecureRequestRedirect(sock, client_address, self)
                return
            tls_connection = TLSConnection(sock)
            if self.handshake(tls_connection):
                self.RequestHandlerClass(tls_connection, client_address, self)
            else:
                # This will probably fail because the TLSConnection has
                # already written SSL stuff to the socket. But not sure what
                # else we should do.
                SecureRequestRedirect(sock, client_address, self)

        def handshake(self, tls_connection):
            try:
                tls_connection.handshakeServer(certChain=self.certChain,
                                               privateKey=self.privateKey,
                                               sessionCache=self.sessionCache)
                tls_connection.ignoreAbruptClose = True
                return True
            except:
                return False


def memoryProfileDecorator(func, profile):
    """ Return a profiled function """
    def profiledFunction(*args, **kw):
        profile.addRequest()
        return func(*args, **kw)
    return profiledFunction


def hotshotProfileDecorator(func, profile):
    """ Return a profiled function """
    profile.moin_requests_done = 0
    def profiledFunction(*args, **kw):
        profile.moin_requests_done += 1
        if profile.moin_requests_done == 1:
            # Don't profile first request, its not interesting
            return func(*args, **kw)
        return profile.runcall(func, *args, **kw)

    return profiledFunction


def quit(signo, stackframe):
    """ Signal handler for aborting signals """
    global httpd, config
    logging.info("Thanks for using MoinMoin!")

    fname = config.pycallgraph_output
    if fname:
        import pycallgraph
        if fname.endswith('.png'):
            pycallgraph.make_dot_graph(fname)
        elif fname.endswith('.dot'):
            pycallgraph.save_dot(fname)

    if httpd:
        httpd.die()


def registerSignalHandlers(func):
    """ Register signal handlers on platforms that support it """
    try:
        import signal
        signal.signal(signal.SIGABRT, func)
        signal.signal(signal.SIGINT, func)
        signal.signal(signal.SIGTERM, func)
    except ImportError:
        pass


def makeServer(config):
    """ Create a new server, based on the the platform capabilities

    Try to create the server class specified in the config. If threads
    are not available, fallback to ForkingServer. If fork is not
    available, fallback to a SimpleServer.
    """
    serverClass = globals()[config.serverClass]
    if serverClass.use_threads:
        try:
            import threading
        except ImportError:
            serverClass = ForkingServer
    if serverClass is ForkingServer and not hasattr(os, "fork"):
        serverClass = SimpleServer
    if serverClass.__name__ != config.serverClass:
        logging.error('%s is not available on this platform, falling back '
                      'to %s\n' % (config.serverClass, serverClass.__name__))

    from MoinMoin import config as _config
    _config.use_threads = serverClass.use_threads
    return serverClass(config)

# ------------------------------------------------------------------------
# Public interface

class StandaloneConfig(Config):
    """ Standalone server default config """
    name = 'moin'
    properties = {}
    docs = '/usr/share/moin/htdocs'
    user = 'www-data'
    group = 'www-data'
    port = 8000
    interface = 'localhost'

    # Advanced options
    serverClass = 'ThreadPoolServer'
    threadLimit = 10
    # The size of the listen backlog. Twisted uses a default of 50.
    # Tests on Mac OS X show many failed request with backlog of 5 or 10.
    requestQueueSize = 50

    # Development options
    memoryProfile = None
    hotshotProfile = None
    cProfile = None # internal use only
    cProfileProfile = None
    pycallgraph_output = None

def cProfileDecorator(func, profile):
    """ Return a profiled function """
    profile.moin_requests_done = 0
    def profiledFunction(*args, **kw):
        profile.moin_requests_done += 1
        if profile.moin_requests_done == 1:
            # Don't profile first request, it's not interesting
            return func(*args, **kw)
        return profile.runcall(func, *args, **kw)

    return profiledFunction

def run(configClass):
    """ Create and run a moin server

    See StandaloneConfig for available options

    @param configClass: config class
    """
    # Run only once!
    global httpd, config
    if httpd is not None:
        raise RuntimeError("You can run only one server per process!")

    config = configClass()

    if config.hotshotProfile and config.cProfileProfile:
        raise RuntimeError("You cannot run two profilers simultaneously.")

    # Install hotshot profiled serve_moin method. To compare with other
    # servers, we profile the part that create and run the request.
    if config.hotshotProfile:
        import hotshot
        config.hotshotProfile = hotshot.Profile(config.hotshotProfile)
        MoinRequestHandler.serve_moin = hotshotProfileDecorator(
            MoinRequestHandler.serve_moin, config.hotshotProfile)

    if config.cProfileProfile:
        import cProfile
        # Create a new cProfile.Profile object using config.cProfileProfile
        # as the path for the output file.
        config.cProfile = cProfile.Profile()
        MoinRequestHandler.serve_moin = cProfileDecorator(
            MoinRequestHandler.serve_moin, config.cProfile)

    # Install a memory profiled serve_moin method
    if config.memoryProfile:
        config.memoryProfile.sample()
        MoinRequestHandler.serve_moin = memoryProfileDecorator(
            MoinRequestHandler.serve_moin, config.memoryProfile)

    # initialize pycallgraph, if wanted
    if config.pycallgraph_output:
        try:
            import pycallgraph
            pycallgraph.settings['include_stdlib'] = False
            pcg_filter = pycallgraph.GlobbingFilter(exclude=['pycallgraph.*',
                                                             'unknown.*',
                                                    ],
                                                    max_depth=9999)
            pycallgraph.start_trace(reset=True, filter_func=pcg_filter)
        except ImportError:
            config.pycallgraph_output = None


    registerSignalHandlers(quit)
    httpd = makeServer(config)

    # Run as a safe user (posix only)
    if os.name == 'posix' and os.getuid() == 0:
        switchUID(config.uid, config.gid)

    httpd.serve_forever()

