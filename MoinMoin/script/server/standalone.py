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
from MoinMoin.server.server_standalone import StandaloneConfig
from MoinMoin.server.daemon import Daemon
from MoinMoin.wsgiapp import run_server

class PluginScript(MoinScript):
    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--docs", dest="docs",
            help="Set the documents directory. Default: wiki/htdocs or /usr/share/moin/htdocs"
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
            "--reload", dest="reload", action="store_true",
            help="Reload the server if there are changes to any loaded python files"
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
                from wikiconfig import Config
            except ImportError, err:
                if 'Config' in str(err):
                    # we are unable to import Config
                    Config = DefaultConfig
                else:
                    # some other import went wrong
                    raise

            if self.options.docs:
                Config.docs = self.options.docs
            if self.options.user:
                Config.user = self.options.user
            if self.options.port:
                Config.port = self.options.port
            if self.options.interface:
                Config.interface = self.options.interface

            if not hasattr(Config, 'docs'):
                docs = os.path.join('wiki', 'htdocs')
                if not os.path.exists(docs):
                    docs = "/usr/share/moin/htdocs"
                Config.docs = docs

            Config.reload_server = self.options.reload

            if self.options.start:
                daemon = Daemon('moin', pidfile, run_server, Config)
                daemon.do_start()
            else:
                run_server(Config)

class DefaultConfig(StandaloneConfig):
    docs = os.path.join('wiki', 'htdocs')
    if not os.path.exists(docs):
        docs = "/usr/share/moin/htdocs"
    user = ''
    group = ''
    port = 8080
    interface = 'localhost'
