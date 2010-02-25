# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - static files and serving them

    MoinMoin uses some static files, like css, js, images, applets etc. and
    they need to get served somehow.

    How does moin use the static files?
    -----------------------------------
    Well, in fact, the moin wiki engine code does not access those files at all,
    it just emits URLs to those files, so the browser of the wiki user will load
    these files by requesting them from these URLs.

    To generate correct URLs to these files, moin uses 2 configuration settings:
    url_prefix_static - this the URL moin uses to generate URLs for static files,
                        default: '/moin_staticXYZ' for moin version X.Y.Z
    url_prefix_local - same thing, but some stuff is required to be on same server
                       or the browser will reject it (e.g. FCKeditor javascript).
                       So, if you point url_prefix_static to another server, you
                       will have to give url_prefix_local with a URL on the same
                       server.

    Where are the static files located on your disk?
    ------------------------------------------------
    You can:
    * Just serve our builtin static stuff from STATIC_FILES_PATH (in the moin code
      at MoinMoin/web/static/htdocs) - in that case you should not modify the
      files or your modifications could be overwritten when you upgrade moin.
    * Copy that stuff to somewhere else and modify it THERE and use it from
      THERE.

    How to serve those static files?
    --------------------------------
    * Let moin serve them at <script_root>/moin_staticXYZ (this is the easiest
      way, you can optimize it later) and use that by setting:
      * for wikis running at root URL (/):
        url_prefix_static = '/moin_staticXYZ' # this is the default!
      * for wikis running at a non-root URL (like e.g. /mymoin):
        from MoinMoin import config
        url_prefix_static = '/mymoin' + config.url_prefix_static
    * Later, you can serve them with your web server (e.g. apache) - you need to
      configure apache to serve the url_prefix_static URL with the files from the
      static files path.

    @copyright: 2009 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from os.path import join, abspath, dirname, isdir

from MoinMoin import config

from werkzeug import SharedDataMiddleware

STATIC_FILES_PATH = join(abspath(dirname(__file__)), 'htdocs')


def make_static_serving_app(application, shared):
    """
    wrap application in a static file serving app

    @param application: WSGI wiki application that should be wrapped
    @param shared:  directory where static files are located (then we create the
                    usual mapping dict we need automatically), or a ready-to-use
                    mapping dict for SharedDataMiddleware.
                    If True, use builtin static files from STATIC_FILES_PATH.
    @returns: wrapped WSGI application
    """
    if not isinstance(shared, dict):
        if shared is True:
            shared = STATIC_FILES_PATH
        if isdir(shared):
            shared = {config.url_prefix_static: shared,
                      # XXX only works / makes sense for root-mounted wikis:
                      '/favicon.ico': join(shared, 'favicon.ico'),
                      '/robots.txt': join(shared, 'robots.txt')}
        else:
            raise ValueError("Invalid path given for shared parameter")
    return SharedDataMiddleware(application, shared)

