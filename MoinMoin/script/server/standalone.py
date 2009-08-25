# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - run standalone server, optionally daemonizing it

    @copyright: 2008 MoinMoin:ForrestVoight
    @license: GNU GPL, see COPYING for details.
"""

import os
import sys
import signal

from MoinMoin.script import MoinScript
from MoinMoin.util.daemon import Daemon
from MoinMoin.web.serving import run_server

class PluginScript(MoinScript):
    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--docs", dest="docs",
            help="Set the documents directory. Default: use builtin MoinMoin/web/static/htdocs"
        )
        self.parser.add_option(
            "--user", dest="user",
            help="Set the user to change to. UNIX only. Default: Don't change"
        )
        self.parser.add_option(
            "--group", dest="group",
            help="Set the group to change to. UNIX only. Default: Don't change"
        )
        self.parser.add_option(
            "--port", dest="port", type="int",
            help="Set the port to listen on. Default: 8080"
        )
        self.parser.add_option(
            "--hostname", "--interface", dest="hostname",
            help="Set the ip/hostname to listen on. Use \"\" for all interfaces. Default: localhost"
        )
        self.parser.add_option(
            "--start", dest="start", action="store_true",
            help="Start server in background."
        )
        self.parser.add_option(
            "--stop", dest="stop", action="store_true",
            help="Stop server in background."
        )
        self.parser.add_option(
            "--pidfile", dest="pidfile",
            help="Set file to store pid of moin daemon in. Default: moin.pid"
        )
        self.parser.add_option(
            "--debug", dest="debug",
            help="Debug mode of server. off: no debugging (default), web: for browser based debugging, external: for using an external debugger."
        )

    def mainloop(self):
        # we don't expect non-option arguments
        if self.args:
            self.parser.error("incorrect number of arguments")

        pidfile = "moin.pid"
        if self.options.pidfile:
            pidfile = self.options.pidfile

        if self.options.stop:
            try:
                pids = open(pidfile, "r").read()
            except IOError:
                print "pid file not found (server not running?)"
            else:
                try:
                    os.kill(int(pids), signal.SIGTERM)
                except OSError:
                    print "kill failed (server not running?)"
            os.remove(pidfile)
        else:
            try:
                if self.options.config_dir:
                    sys.path.insert(0, self.options.config_dir)
                from wikiserverconfig import Config
            except ImportError, err:
                if 'wikiserverconfig' in str(err):
                    # we are unable to import from wikiserverconfig module
                    Config = DefaultConfig
                else:
                    # some other import went wrong
                    raise

            # intialize some defaults if missing
            kwargs = {}
            for option in ('user', 'group',
                           'hostname', 'port',
                           'threaded', 'processes',
                           'debug', 'use_evalex',
                           'use_reloader', 'extra_files', 'reloader_interval',
                           'docs', 'static_files', ):
                if hasattr(Config, option):
                    kwargs[option] = getattr(Config, option)
                else:
                    # usually inheriting from DefaultConfig should make this superfluous,
                    # but who knows what users write into their config...
                    kwargs[option] = getattr(DefaultConfig, option)

            # override config settings with cmdline options:
            if self.options.docs:
                kwargs['docs'] = self.options.docs
            if self.options.user:
                kwargs['user'] = self.options.user
            if self.options.group:
                kwargs['group'] = self.options.group
            if self.options.debug:
                kwargs['debug'] = self.options.debug

            if self.options.hostname is not None: # needs to work for "" value also
                kwargs['hostname'] = self.options.hostname
            if self.options.port:
                kwargs['port'] = self.options.port

            if self.options.start:
                daemon = Daemon('moin', pidfile, run_server, **kwargs)
                daemon.do_start()
            else:
                run_server(**kwargs)


class DefaultConfig(object):
    # where the static data is served from - you can either use:
    # docs = True  # serve the builtin static data from MoinMoin/web/static/htdocs/
    # docs = '/where/ever/you/like/to/keep/htdocs'  # serve it from the given path
    # docs = False  # do not serve static files at all (will not work except
    #               # you serve them in some other working way)
    docs = True

    # user and group to run moin as:
    user = None
    group = None

    # debugging options: 'off', 'web', 'external'
    debug = 'off'

    # should the exception evaluation feature be enabled?
    use_evalex = True

    # Werkzeug run_simple arguments below here:

    # hostname/ip and port the server listens on:
    hostname = 'localhost'
    port = 8080

    # either multi-thread or multi-process (not both):
    # threaded = True, processes = 1 is usually what you want
    # threaded = False, processes = 10 (for example) can be rather slow
    # thus, if you need a forking server, maybe rather use apache/mod-wsgi!
    threaded = True
    processes = 1

    # automatic code reloader - needs testing!
    use_reloader = False
    extra_files = None
    reloader_interval = 1

    # we can't use static_files to replace our own middleware setup for moin's
    # static files, because we also need the setup with other servers (like
    # apache), not just when using werkzeug's run_simple server.
    # But you can use it if you need to serve other static files you just need
    # with the standalone wikiserver.
    static_files = None

