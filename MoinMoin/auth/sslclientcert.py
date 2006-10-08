# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - SSL client certificate authentication

    Currently not supported for Twisted web server, but only for web servers
    setting SSL_CLIENT_* environment (e.g. Apache).
    
    @copyright: 2006 by MoinMoin:ThomasWaldmann,
                2003 by Martin v. Löwis
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import config, user
from MoinMoin.request import TWISTED

def sslclientcert(request, **kw):
    """ authenticate via SSL client certificate """
    user_obj = kw.get('user_obj')
    u = None
    changed = False
    # check if we are running Twisted
    if isinstance(request, TWISTED.Request):
        return user_obj, True # not supported if we run twisted
        # Addendum: this seems to need quite some twisted insight and coding.
        # A pointer i got on #twisted: divmod's vertex.sslverify
        # If you really need this, feel free to implement and test it and
        # submit a patch if it works.
    else:
        env = request.env
        if env.get('SSL_CLIENT_VERIFY', 'FAILURE') == 'SUCCESS':
            # if we only want to accept some specific CA, do a check like:
            # if env.get('SSL_CLIENT_I_DN_OU') == "http://www.cacert.org"
            email = env.get('SSL_CLIENT_S_DN_Email', '').decode(config.charset)
            email_lower = email.lower()
            commonname = env.get('SSL_CLIENT_S_DN_CN', '').decode(config.charset)
            commonname_lower = commonname.lower()
            if email_lower or commonname_lower:
                for uid in user.getUserList(request):
                    u = user.User(request, uid,
                                  auth_method='sslclientcert', auth_attribs=())
                    if email_lower and u.email.lower() == email_lower:
                        u.auth_attribs = ('email', 'password')
                        #this is only useful if same name should be used, as
                        #commonname is likely no CamelCase WikiName
                        #if commonname_lower != u.name.lower():
                        #    u.name = commonname
                        #    changed = True
                        #u.auth_attribs = ('email', 'name', 'password')
                        break
                    if commonname_lower and u.name.lower() == commonname_lower:
                        u.auth_attribs = ('name', 'password')
                        #this is only useful if same email should be used as
                        #specified in certificate.
                        #if email_lower != u.email.lower():
                        #    u.email = email
                        #    changed = True
                        #u.auth_attribs = ('name', 'email', 'password')
                        break
                else:
                    u = None
                if u is None:
                    # user wasn't found, so let's create a new user object
                    u = user.User(request, name=commonname_lower, auth_username=commonname_lower)

    if u:
        u.create_or_update(changed)
    if u and u.valid:
        return u, True
    else:
        return user_obj, True

