# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - logging auth plugin

    This does nothing except logging the auth parameters (the password is NOT
    logged, of course).

    @copyright: 2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

def log(request, **kw):
    """ just log the call, do nothing else """
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    logout = kw.get('logout')
    user_obj = kw.get('user_obj')
    request.log("auth.log: name=%s login=%r logout=%r user_obj=%r" % (username, login, logout, user_obj))
    return user_obj, True

