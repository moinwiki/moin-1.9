# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.packages tests - common code

    @copyright: 2007 MoinMoin:KarolNowak
    @license: GNU GPL, see COPYING for details.
"""

def gain_superuser_rights(request):
    request.user.name = "SuperUserName"
    request.user.valid = 1
    request.user.may.name = request.user.name
    request.cfg.superuser.append(request.user.name)
    request.user.auth_method = request.cfg.auth_methods_trusted[0]
