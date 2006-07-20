# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - test action

    This action allows you to run some tests and show some data about your system.

    If you don't want this action to be available due to system privacy reasons,
    do this in your wiki/farm config:

    actions_excluded = ["test"]
    
    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import os, sys

from MoinMoin import config, version
from MoinMoin.action import ActionBase
from MoinMoin.logfile import editlog, eventlog


def runTest(request):
    request.write('Release %s\n' % version.release)
    request.write('Revision %s\n' % version.revision)
    request.write('Python version %s\n' % sys.version)
    request.write('Python installed to %s\n' % sys.exec_prefix)

    # Try xml
    try:
        import xml
        request.write('PyXML is %sinstalled\n' % ('NOT ', '')[xml.__file__.find('_xmlplus') != -1])
    except ImportError:
        request.write('PyXML is missing\n')

    request.write('Python Path:\n')
    for dir in sys.path:
        request.write('   %s\n' % dir)

    # check if the request is a local one
    import socket
    local_request = (socket.getfqdn(request.server_name) == socket.getfqdn(request.remote_addr))

    # check directories
    request.write("Checking directories...\n")
    dirs = [('data', request.cfg.data_dir),
            ('user', request.cfg.user_dir),
           ]
    for name, path in dirs:
        if not os.path.isdir(path):
            request.write("*** %s directory NOT FOUND (set to '%s')\n" % (name, path))
        elif not os.access(path, os.R_OK | os.W_OK | os.X_OK):
            request.write("*** %s directory NOT ACCESSIBLE (set to '%s')\n" % (name, path))
        else:
            path = os.path.abspath(path)
            request.write("    %s directory tests OK (set to '%s')\n" % (name, path))

    # check eventlog access
    log = eventlog.EventLog(request)
    msg = log.sanityCheck()
    if msg: request.write("*** %s\n" % msg)

    # check editlog access
    log = editlog.EditLog(request)
    msg = log.sanityCheck()
    if msg: request.write("*** %s\n" % msg)

    # keep some values to ourselves
    request.write("\nServer Environment:\n")
    if local_request:
        # print the environment, in case people use exotic servers with broken
        # CGI APIs (say, M$ IIS), to help debugging those
        keys = os.environ.keys()
        keys.sort()
        for key in keys:
            request.write("    %s = %s" % (key, repr(os.environ[key])))
    else:
        request.write("    ONLY AVAILABLE FOR LOCAL REQUESTS ON THIS HOST!")

    # run unit tests
    request.write("\n\nUnit Tests:\n")

    # The unit tests are diabled on servers using threads, beause they
    # change request.cfg, which is now shared between threads.
    # TODO: check if we can enable them back in a safe way
    if config.use_threads:
        request.write("    *** The unit tests are disabled when using multi "
                      "threading ***")
    else:
        # TODO: do we need to hide the error when _tests can't be
        # imported? It might make it hard to debug the tests package
        # itself.
        try:
            from MoinMoin import _tests
        except ImportError:
            request.write("    *** The unit tests are not available ***")
        else:
            _tests.run(request)

class test(ActionBase):
    """ test and show info action

    Note: the action name is the class name
    """
    def do_action(self):
        """ run tests """
        request = self.request
        request.http_headers(["Content-type: text/plain; charset=%s" % config.charset])
        request.write('MoinMoin Diagnosis\n======================\n\n')
        runTest(request)
        return True, ""

    def do_action_finish(self, success):
        """ we don't want to do the default stuff, but just NOTHING """
        pass

def execute(pagename, request):
    """ Glue code for actions """
    test(pagename, request).render()

