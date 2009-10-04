# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Filter Package

    @copyright: 2006-2009 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import sys, os
import time

try:
    # requires Python >= 2.4
    import subprocess
except ImportError:
    subprocess = None

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.util import pysupport

modules = pysupport.getPackageModules(__file__)

standard_codings = ['utf-8', 'iso-8859-15', 'iso-8859-1', ]


def quote_filename(filename):
    """ quote a filename (could contain blanks or other special chars) in a
        way suitable for the platform we run on.
    """
    # XXX Use os.name AND/OR sys.platform?
    if os.name == 'posix':
        filename = "'%s'" % filename
    elif sys.platform == 'win32':
        filename = '"%s"' % filename
    else:
        raise ValueError("MoinMoin.filter.quote_filename: os/platform not supported")
    return filename


def exec_cmd(cmd, timeout=300):
    logging.debug("Trying to start command: %s" % cmd)
    if subprocess:
        tstart = time.time()
        p = subprocess.Popen(cmd, shell=True,
                             close_fds=not subprocess.mswindows,
                             bufsize=1024,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        child_stdin, child_stdout, child_stderr = p.stdin, p.stdout, p.stderr

        tmax = tstart + timeout
        tnow = time.time()
        data = []
        errors = []
        rc = None
        while rc is None and tnow < tmax:
            time.sleep(0.001) # wait at least 1ms between polls
            data.append(child_stdout.read())
            errors.append(child_stderr.read())
            rc = p.poll()
            tnow = time.time()

        child_stdout.close()
        child_stderr.close()

        data = ''.join(data)
        errors = ''.join(errors)

        t = tnow - tstart
        if rc is None:
            logging.warning("Command '%s' timed out (%fs)" % (cmd, t))
            rc = terminate(p)

        if rc < 0:
            logging.warning("Command '%s' was terminated by signal %d (%fs)" % (cmd, -rc, t))
        elif rc > 0:
            logging.warning("Command '%s' terminated with rc=%d (%fs)" % (cmd, rc, t))
        else:
            logging.debug("Command '%s' terminated normally rc=%d (%fs)" % (cmd, rc, t))

    else:
        child_stdin, child_stdout, child_stderr = os.popen3(cmd)
        data = child_stdout.read()
        errors = child_stderr.read()
        child_stdout.close()
        child_stderr.close()

    logging.debug("Command '%s', stderr: %s, stdout: %d bytes" % (cmd, errors, len(data)))
    return data, errors


def terminate(proc):
    """ subprocess.Popen.terminate is not implemented on some Windows python versions.
        This workaround works on both POSIX and Windows.
        Originally from: Guillaume Rava, http://code.activestate.com/recipes/576667/
        terminate also seems to be only implemented in Python >= 2.6.
    """
    try:
        proc.terminate()
    except AttributeError:
        if not subprocess.mswindows:
            import signal
            os.kill(proc.pid, signal.SIGTERM)
        else:
            try:
                import win32api
            except ImportError:
                logging.warning("could not import win32api, please install win32 extensions")
            else:
                PROCESS_TERMINATE = 1
                handle = win32api.OpenProcess(PROCESS_TERMINATE, False, proc.pid)
                win32api.TerminateProcess(handle, -1)
                win32api.CloseHandle(handle)
    return proc.wait() # wait until it is really dead


def execfilter(cmd, filename, codings=standard_codings):
    """ use cmd to get plaintext content of filename
        to decode to unicode, we use the first coding of codings list that
        does not throw an exception or force ascii
    """
    filter_cmd = cmd % quote_filename(filename)
    data, errors = exec_cmd(filter_cmd)
    for c in codings:
        try:
            return data.decode(c)
        except UnicodeError:
            pass
    return data.decode('ascii', 'replace')

