# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - http authentication

    You need either your webserver configured for doing HTTP auth (like Apache
    reading some .htpasswd file) or Twisted (will accept HTTP auth against
    password stored in moin user profile, but currently will NOT ask for auth).

    @copyright: 2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import user
from MoinMoin.request import TWISTED, CLI

def http(request, **kw):
    """ authenticate via http basic/digest/ntlm auth """
    user_obj = kw.get('user_obj')
    u = None
    # check if we are running Twisted
    if isinstance(request, TWISTED.Request):
        username = request.twistd.getUser()
        password = request.twistd.getPassword()
        # when using Twisted http auth, we use username and password from
        # the moin user profile, so both can be changed by user.
        u = user.User(request, auth_username=username, password=password,
                      auth_method='http', auth_attribs=())

    elif not isinstance(request, CLI.Request):
        env = request.env
        auth_type = env.get('AUTH_TYPE','')
        if auth_type in ['Basic', 'Digest', 'NTLM', 'Negotiate',]:
            username = env.get('REMOTE_USER','')
            if auth_type in ('NTLM', 'Negotiate',):
                # converting to standard case so the user can even enter wrong case
                # (added since windows does not distinguish between e.g.
                #  "Mike" and "mike")
                username = username.split('\\')[-1] # split off domain e.g.
                                                    # from DOMAIN\user
                # this "normalizes" the login name from {meier, Meier, MEIER} to Meier
                # put a comment sign in front of next line if you don't want that:
                username = username.title()
            # when using http auth, we have external user name and password,
            # we don't use the moin user profile for those attributes.
            u = user.User(request, auth_username=username,
                          auth_method='http', auth_attribs=('name', 'password'))

    if u:
        u.create_or_update()
    if u and u.valid:
        return u, True # True to get other methods called, too
    else:
        return user_obj, True

