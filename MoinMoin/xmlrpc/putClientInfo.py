"""
    This is a wiki xmlrpc plugin doing some usage logging.
    It enables server admins to see how many clients use xmlrpc how often.
    It also helps MoinMoin development team  to improve xmlrpc stuff and get
    some statistics about MoinMoin usage.

    @copyright: 2004 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, time

def execute(xmlrpcobj, action, site):
    t = time.time()
    logentry = '%d %s %s\n' % (t, action, site)
    log = open(os.path.join(xmlrpcobj.request.cfg.data_dir, 'xmlrpc-log'), 'a')
    log.write(logentry)
    log.close()
    return 0

