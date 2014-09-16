# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Filter Package

    @copyright: 2006-2009 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import sys, os
import time

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.util import pysupport

modules = pysupport.getPackageModules(__file__)

standard_codings = ['utf-8', 'iso-8859-15', 'iso-8859-1', ]

from MoinMoin.util.SubProcess import exec_cmd


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


def execfilter(cmd, filename, codings=standard_codings):
    """ use cmd to get plaintext content of filename
        to decode to unicode, we use the first coding of codings list that
        does not throw an exception or force ascii
    """
    filter_cmd = cmd % quote_filename(filename)
    data, errors, rc = exec_cmd(filter_cmd, timeout=300)
    logging.debug("Command '%s', rc: %d, stdout: %d bytes, stderr: %s" % (filter_cmd, rc, len(data), errors))
    for c in codings:
        try:
            return data.decode(c)
        except UnicodeError:
            pass
    return data.decode('ascii', 'replace')

