# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI middlewares for profiling

    These have been ported from server_standalone to provide application
    profiling for MoinMoin.wsgiapp

    @copyright: 2008 MoinMoin:FlorianKrupicka,

    @license: GNU GPL, see COPYING for details.
"""
from werkzeug.utils import get_current_url

from MoinMoin import log
logging = log.getLogger(__name__)

class ProfilerMiddleware(object):
    def __init__(self, app):
        self.app = app

    def profile(self, environ, start_response):
        method = environ.get('REQUEST_METHOD', 'GET')
        url = get_current_url(environ)
        logging.debug("Profiling call for '%s %s'", method, url)
        try:
            res = self.run_profile(self.app, (environ, start_response))
        except Exception, e:
            logging.error("Exception while profiling '%s %s': %r",
                          method, url, e)
            raise
        return res

    __call__ = profile

    def run_profile(self, app, *args, **kwargs):
        """ Override in subclasses. Call signature tries to compatible
        with common profilers .runcall methods.
        """
        raise NotImplementedError()

    def shutdown(self):
        """ Override in subclasses to clean up when server/script
        shuts down.
        """
        pass

class CProfileMiddleware(ProfilerMiddleware):
    def __init__(self, app, filename):
        super(CProfileMiddleware, self).__init__(app)
        import cProfile
        self._profile = cProfile.Profile()
        self._filename = filename
        self.run_profile = self._profile.runcall

    def shutdown(self):
        self._profile.dump_stats(self._filename)

class HotshotMiddleware(ProfilerMiddleware):
    def __init__(self, app, *args, **kwargs):
        super(HotshotMiddleware, self).__init__(app)
        import hotshot
        self._profile = hotshot.Profile(*args, **kwargs)
        self.run_profile = self._profile.runcall

    def shutdown(self):
        self._profile.close()

class PycallgraphMiddleware(ProfilerMiddleware):
    def __init__(self, app, filename):
        super(PycallgraphMiddleware, self).__init__(app)
        import pycallgraph
        pycallgraph.settings['include_stdlib'] = False
        self._filename = filename
        globs = ['pycallgraph.*', 'unknown.*']
        f = pycallgraph.GlobbingFilter(exclude=globs, max_depth=9999)
        self._filter = f
        self.pycallgraph = pycallgraph

    def run_profile(self, app, *args, **kwargs):
        pycallgraph = self.pycallgraph
        pycallgraph.start_trace(reset=True, filter_func=self._filter)
        try:
            return app(*args, **kwargs)
        finally:
            pycallgraph.stop_trace()

    def shutdown(self):
        fname = self._filename
        pycallgraph = self.pycallgraph
        if fname.endswith('.png'):
            logging.info("Saving the rendered callgraph to '%s'", fname)
            pycallgraph.make_dot_graph(fname)
        elif fname.endswith('.dot'):
            logging.info("Saving the raw callgraph to '%s'", fname)
            pycallgraph.save_dot(fname)
