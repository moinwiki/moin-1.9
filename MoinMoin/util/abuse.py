# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - (ab)use logging
    Log some data that can be used for usage analysis and abuse detection.

    This logging functionality is kept in this separate module so we can
    easily redirect the output to a separate log using logging configuration.

    @copyright: 2013 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)


def log_attempt(system, success, request=None, username=None, pagename=None):
    """
    log attempts to use <system>, log success / failure / username / ip

    @param system: some string telling about the system that was used, e.g.
                   "auth/login" or "textcha"
    @param success: whether the attempt was successful
    @param request: request object (optional, to determine remote's ip address)
    @param username: user's name (optional, if None: determined from request)
    @param pagename: name of the page (optional)
    """
    if username is None:
        if request and hasattr(request, 'user') and request.user.valid:
            username = request.user.name
        else:
            username = u'anonymous'
    level = (logging.WARNING, logging.INFO)[success]
    msg = """: %s: status %s: username "%s": ip %s: page %s"""
    status = ("failure", "success")[success]
    ip = request and request.remote_addr or 'unknown'
    logging.log(level, msg, system, status, username, ip, pagename)
