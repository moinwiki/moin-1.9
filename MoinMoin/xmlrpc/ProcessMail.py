# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - This plugin is used for multi-tier mail processing

    @copyright: 2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.mail import mailimport

def execute(xmlrpcobj, secret, mail):
    request = xmlrpcobj.request
    secret = xmlrpcobj._instr(secret)
    mail = str(mail)

    if not request.cfg.mail_import_secret:
        return u"No password set"

    if request.cfg.mail_import_secret != secret:
        return u"Invalid password"

    try:
        mailimport.import_mail_from_string(request, mail)
    except mailimport.ProcessingError, e:
        err = u"An error occured while processing the message: " + str(e.args)
        request.log(err)
        return xmlrpcobj._outstr(err)
    return xmlrpcobj._outstr(u"OK")
