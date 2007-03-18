# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Remote Script Execution Server part

    @copyright: 2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script import MoinScript

def execute(xmlrpcobj, their_secret, argv):
    request = xmlrpcobj.request
    their_secret = xmlrpcobj._instr(their_secret)

    our_secret = request.cfg.remote_script_secret
    if not our_secret:
        return u"No password set"

    if our_secret != their_secret:
        return u"Invalid password"

    try:
        request.log("RemoteScript argv: %r" % argv)
        MoinScript(argv).run(showtime=0)
    except Exception, err:
        e = str(err)
        request.log(e)
        return xmlrpcobj._outstr(e)
    return xmlrpcobj._outstr(u"OK")

