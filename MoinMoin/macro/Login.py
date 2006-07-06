# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - login form

    @copyright: 2005-2006 by Radomirs Cirskis <nad2000@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.widget import html
from MoinMoin import userform

def execute(macro, args):
    """ Show the login form (but only when not logged in) """
    request = macro.request
    if request.user.valid:
        data = u''
    else:
        data = userform.getLogin(request)
    return data

