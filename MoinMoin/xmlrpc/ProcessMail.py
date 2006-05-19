# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - This plugin is used for multi-tier mail processing

    @copyright: 2006 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import mailimport

def execute(xmlrpcobj, secret, mail):
    request = xmlrpcobj.request
    secret = xmlrpcobj._instr(secret)
    # hmm, repeated re-encoding looks suboptimal in terms of speed
    mail = xmlrpcobj._instr(mail).encode("utf-8") 
    
    if request.cfg.email_secret != secret:
        return u"Invalid password"
    
    try:
        mailimport.import_mail_from_string(request, mail)
    except mailimport.ProcessingError, e:
        err = u"An error occured while processing the message: " + str(e.args)
        request.log(err)
        return xmlrpcobj._outstr(err)
    return xmlrpcobj._outstr(u"OK")
