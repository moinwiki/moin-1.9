# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Command line utilities

    @copyright: 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os, sys, time

flag_quiet = 0
script_module = '__main__'

#############################################################################
### Logging
#############################################################################

def fatal(msgtext, **kw):
    """ Print error msg to stderr and exit. """
    sys.stderr.write("FATAL ERROR: " + msgtext + "\n")
    if kw.get('usage', 0):
        maindict = vars(sys.modules[script_module])
        if maindict.has_key('usage'):
            maindict['usage']()
    sys.exit(1)


def log(msgtext):
    """ Optionally print error msg to stderr. """
    if not flag_quiet:
        sys.stderr.write(msgtext + "\n")


#############################################################################
### Commandline Support
#############################################################################

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

        cmd = self.script_module.__name__.split('.')[-1].replace('_', '-')
        rev = "%s %s [%s]" % (version.project, version.release, version.revision)
        sys.argv[0] = cmd

        self.parser = optparse.OptionParser(
            usage="%(cmd)s %(usage)s\n\n" % {'cmd': cmd, 'usage': usage, },
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
        from MoinMoin.request import RequestCLI
        if self.options.wiki_url:
            self.request = RequestCLI(self.options.wiki_url, self.options.page)
        else:
            self.request = RequestCLI(pagename=self.options.page)
        
    def mainloop(self):
        # Insert config dir or the current directory to the start of the path.
        config_dir = self.options.config_dir
        if config_dir and not os.path.isdir(config_dir):
            fatal("bad path given to --config-dir option")
        sys.path.insert(0, os.path.abspath(config_dir or os.curdir))

        args = self.args
        if len(args) < 2:
            self.parser.error("you must specify a command module and name.")
            sys.exit(1)

        cmd_module, cmd_name = args[:2]
        from MoinMoin import wikiutil
        plugin_class = wikiutil.importBuiltinPlugin('script.%s' % cmd_module, cmd_name, 'PluginScript')
        plugin_class(args[2:], self.options).run() # all starts again there

