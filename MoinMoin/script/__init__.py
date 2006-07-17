# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Extension Script Package

    @copyright: 2000-2002 by Jürgen Hermann <jh@web.de>,
                2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport

# create a list of extension scripts from the subpackage directory
extension_scripts = pysupport.getPackageModules(__file__)
modules = extension_scripts

import os, sys, time

flag_quiet = 0
script_module = '__main__'


# ScriptRequest -----------------------------------------------------------

class ScriptRequest(object):
    """this is for scripts (MoinMoin/script/*) running from the commandline (CLI)
       or from the xmlrpc server (triggered by a remote xmlrpc client).

       Every script needs to do IO using this ScriptRequest class object -
       IT IS DIFFERENT from the usual "request" you have in moin (easily to be seen
       when you look at an xmlrpc script invocation: request.write will write to the
       xmlrpc "channel", but scriptrequest.write needs to write to some buffer we
       transmit later as an xmlrpc function return value.
    """
    def __init__(self, instream, outstream, errstream):
        self.instream = instream
        self.outstream = outstrem
        self.errstream = errstream

    def read(self, n=None):
        if n is None:
            data = self.instream.read()
        else:
            data = self.instream.read(n)
        return data

    def write(self, data):
        self.outstream.write(data)

    def write_err(self, data):
        self.errstream.write(data)


class ScriptRequestCLI(ScriptRequest):
    """ When a script runs directly on the shell, we just use the CLI request
        object (see MoinMoin.request.CLI) to do I/O (which will use stdin/out/err).
    """
    def __init__(self, request):
        self.request = request

    def read(self, n=None):
        return self.request.read(n)

    def write(self, data):
        return self.request.write(n)

    def write_err(self, data):
        return self.request.write(n) # XXX use correct request method - log, error, whatever.

class ScriptRequestStrings(ScriptRequest):
    """ When a script gets run by our xmlrpc server, we have the input as a
        string and we also need to catch the output / error output as strings.
    """
    def __init__(self, instr):
        self.instream = StringIO(instr)
        self.outstream = StringIO()
        self.errstream = StringIO()

    def fetch_output(self):
        outstr = self.outstream.get_value()
        errstr = self.errstream.get_value()
        self.outstream.close()
        self.errstream.close()
        return outstr, errstr


# Logging -----------------------------------------------------------------

def fatal(msgtext, **kw):
    """ Print error msg to stderr and exit. """
    sys.stderr.write("\n\nFATAL ERROR: " + msgtext + "\n")
    if kw.get('usage', 0):
        maindict = vars(sys.modules[script_module])
        if maindict.has_key('usage'):
            maindict['usage']()
    sys.exit(1)


def log(msgtext):
    """ Optionally print error msg to stderr. """
    if not flag_quiet:
        sys.stderr.write(msgtext + "\n")


# Commandline Support --------------------------------------------------------

class Script:
    def __init__(self, script, usage, argv=None, def_values=None):
        #print "argv:", argv, "def_values:", repr(def_values)
        if argv is None:
            self.argv = sys.argv[1:]
        else:
            self.argv = argv
        self.def_values = def_values
        self.script_module = sys.modules[script]

        global _start_time
        _start_time = time.clock()

        import optparse
        from MoinMoin import version

        # what does this code do? at least it does not work.
        cmd = self.script_module.__name__.split('.')[-1].replace('_', '-')
        rev = "%s %s [%s]" % (version.project, version.release, version.revision)
        #sys.argv[0] = cmd

        self.parser = optparse.OptionParser(
            usage="%(cmd)s [command] %(usage)s" % {'cmd': os.path.basename(sys.argv[0]), 'usage': usage, },
            version=rev)
        self.parser.allow_interspersed_args = False
        if def_values:
            self.parser.set_defaults(**def_values.__dict__)
        self.parser.add_option(
            "-q", "--quiet",
            action="store_true", dest="quiet",
            help="Be quiet (no informational messages)"
        )
        self.parser.add_option(
            "--show-timing",
            action="store_true", dest="show_timing", default=False,
            help="Show timing values [default: %default]"
        )

    def run(self, showtime=1):
        """ Run the main function of a command. """
        global flag_quiet
        try:
            try:
                self.options, self.args = self.parser.parse_args(self.argv)
                flag_quiet = self.options.quiet
                self.mainloop()
            except KeyboardInterrupt:
                log("*** Interrupted by user!")
            except SystemExit:
                showtime = 0
                raise
        finally:
            if showtime:
                self.logRuntime()

    def logRuntime(self):
        """ Print the total command run time. """
        if self.options.show_timing:
            log("Needed %.3f secs." % (time.clock() - _start_time,))


class MoinScript(Script):
    """ Moin main script class """

    def __init__(self, argv=None, def_values=None):
        Script.__init__(self, __name__, "[options]", argv, def_values)
        # those are options potentially useful for all sub-commands:
        self.parser.add_option(
            "--config-dir", metavar="DIR", dest="config_dir",
            help=("Path to the directory containing the wiki "
                  "configuration files. [default: current directory]")
        )
        self.parser.add_option(
            "--wiki-url", metavar="WIKIURL", dest="wiki_url",
            help="URL of a single wiki to migrate e.g. localhost/mywiki/ [default: CLI]"
        )
        self.parser.add_option(
            "--page", dest="page", default='',
            help="wiki page name [default: %default]"
        )

    def init_request(self):
        """ create request """
        from MoinMoin.request import CLI
        if self.options.wiki_url:
            self.request = CLI.Request(self.options.wiki_url, self.options.page)
        else:
            self.request = CLI.Request(pagename=self.options.page)

    def mainloop(self):
        # Insert config dir or the current directory to the start of the path.
        config_dir = self.options.config_dir
        if config_dir and not os.path.isdir(config_dir):
            fatal("bad path given to --config-dir option")
        sys.path.insert(0, os.path.abspath(config_dir or os.curdir))

        args = self.args
        if len(args) < 2:
            self.parser.print_help()
            fatal("You must specify a command module and name.")

        cmd_module, cmd_name = args[:2]
        from MoinMoin import wikiutil
        try:
            plugin_class = wikiutil.importBuiltinPlugin('script.%s' % cmd_module, cmd_name, 'PluginScript')
        except wikiutil.PluginMissingError:
            fatal("Command plugin %r, command %r was not found." % (cmd_module, cmd_name))
        plugin_class(args[2:], self.options).run() # all starts again there

