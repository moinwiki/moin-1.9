# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - This plugin is used for multi-tier mail processing

    @copyright: 2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.mail import mailimport

def execute(xmlrpcobj, secret, mail):
    request = xmlrpcobj.request
    secret = xmlrpcobj._instr(secret)
    mail = str(mail)

    if request.cfg.secrets['xmlrpc/ProcessMail'] != secret:
        return u"Invalid password"

    try:
        mailimport.import_mail_from_string(request, mail)
    except mailimport.ProcessingError, e:
        err = u"An error occurred while processing the message: " + str(e.args)
        logging.error(err)
        return xmlrpcobj._outstr(err)
    return xmlrpcobj._outstr(u"OK")
