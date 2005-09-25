# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Command line utilities

    @copyright: 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os, sys

flag_quiet = 0
script_module = '__main__'


#############################################################################
### Logging
#############################################################################

def fatal(msgtext, **kw):
    """ Print error msg to stderr and exit.
    """
    sys.stderr.write("FATAL ERROR: " + msgtext + "\n")
    if kw.get('usage', 0):
        maindict = vars(sys.modules[script_module])
        if maindict.has_key('usage'):
            maindict['usage']()
    sys.exit(1)


def log(msgtext):
    """ Optionally print error msg to stderr.
    """
    if not flag_quiet:
        sys.stderr.write(msgtext + "\n")


#############################################################################
### Commandline Support
#############################################################################

class Script:

    def __init__(self, script, usage):
        import sys, time

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
        self.parser.add_option(
            "-q", "--quiet", 
            action="store_true", dest="quiet",
            help="Be quiet (no informational messages)"
        )


    def run(self):
        """ Run the main function of a command.
        """
        global flag_quiet

        showtime = 1
        try:
            try:
                self.options, self.args = self.parser.parse_args()
                flag_quiet = self.options.quiet
                self.mainloop()
            except KeyboardInterrupt:
                log("*** Interrupted by user!")
            except SystemExit:
                showtime = 0
                raise
        finally:
            if showtime: self.logRuntime()


    def logRuntime(self):
        """ Print the total command run time.
        """
        import time
        log("Needed %.3f secs." % (time.clock() - _start_time,))

