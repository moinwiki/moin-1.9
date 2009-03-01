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
            "--interface", dest="interface",
            help="Set the ip to listen on. Use \"\" for all interfaces. Default: localhost"
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
            "--debug", dest="debug", action="store_true",
            help="Enable debug mode of server (show tracebacks)"
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
            for option in ('docs', 'user', 'group', 'port', 'interface', 'debug'):
                if not hasattr(Config, option):
                    value = getattr(DefaultConfig, option)
                    setattr(Config, option, value)

            # override with cmdline options
            if self.options.docs:
                Config.docs = self.options.docs
            if self.options.user:
                Config.user = self.options.user
            if self.options.group:
                Config.group = self.options.group
            if self.options.port:
                Config.port = self.options.port
            if self.options.interface is not None: # needs to work for "" value also
                Config.interface = self.options.interface
            if self.options.debug:
                Config.debug = True

            if self.options.start:
                daemon = Daemon('moin', pidfile, run_server, Config)
                daemon.do_start()
            else:
                run_server(Config.interface, Config.port, Config.docs,
                           use_debugger=Config.debug, user=Config.user,
                           group=Config.group)

class DefaultConfig:
    # where the static data is served from - you can either use:
    # docs = True  # serve the builtin static data from MoinMoin/web/static/htdocs/
    # docs = '/where/ever/you/like/to/keep/htdocs'  # serve it from the given path
    # docs = False  # do not serve static files at all (will not work except
    #               # you serve them in some other working way)
    docs = True

    user = None
    group = None
    port = 8080
    interface = 'localhost'
    debug = False

