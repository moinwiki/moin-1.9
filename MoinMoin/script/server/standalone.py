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
from MoinMoin.server.server_standalone import StandaloneConfig, run
from MoinMoin.server.daemon import Daemon

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
            "--serverClass", dest="serverClass",
            help="Set the server model to use. Choices: ThreadPool, serverClass, Forking, Simple. Default: ThreadPool"
        )
        self.parser.add_option(
            "--threadLimit", dest="threadLimit", type="int",
            help="Set the maximum number of threads to use. Default: 10"
        )
        self.parser.add_option(
            "--requestQueueSize", dest="requestQueueSize", type="int",
            help="Set the size of the request queue. Default: 50"
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

    def mainloop(self):
        # we don't expect non-option arguments
        if self.args:
            self.parser.error("incorrect number of arguments")

        if self.options.serverClass:
            thread_choices = ["ThreadPool", "Threading", "Forking", "Simple"]
            thread_choices2 = [x.upper() for x in thread_choices]
            thread_choice = self.options.serverClass.upper()
            try:
                serverClass_index = thread_choices2.index(thread_choice)
            except ValueError:
                self.parser.error("invalid serverClass type")
            serverClass = thread_choices[serverClass_index]
        else:
            serverClass = None

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
            if serverClass:
                Config.serverClass = serverClass + 'Server'
            if self.options.threadLimit:
                Config.threadLimit = self.options.threadLimit
            if self.options.requestQueueSize:
                Config.requestQueueSize = self.options.requestQueueSize

            if self.options.start:
                daemon = Daemon('moin', pidfile, run, Config)
                daemon.do_start()
            else:
                run(Config)

class DefaultConfig(StandaloneConfig):
    docs = os.path.join('wiki', 'htdocs')
    if not os.path.exists(docs):
        docs = "/usr/share/moin/htdocs"
    user = ''
    group = ''
    port = 8080
    interface = 'localhost'
    serverClass = 'ThreadPoolServer'
    threadLimit = 10
    requestQueueSize = 50

