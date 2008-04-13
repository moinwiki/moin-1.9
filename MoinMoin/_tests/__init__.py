# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - some common code for testing

    @copyright: 2007 MoinMoin:KarolNowak,
                2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

def become_known(request, username=u"KnownUser"):
    """ modify request.user to make the user valid, so it is in acl group Known """
    request.user.name = username
    request.user.may.name = username
    request.user.valid = 1

def become_trusted(request, username=u"TrustedUser"):
    """ modify request.user to make the user valid and trusted, so it is in acl group Trusted """
    become_known(request, username)
    request.user.auth_method = request.cfg.auth_methods_trusted[0]

def become_superuser(request):
    """ modify request.user so it is in the superuser list,
        also make the user valid (and thus in "Known" ACL pseudo group),
        also make the user trusted (and thus in "Trusted" ACL pseudo group).

        TODO: check why many tests fail if we just use "become_known" instead
              of "become_trusted". Then refactor to only use "become_known".

        Note: being superuser is completely unrelated to ACL rights,
              especially it is not related to ACL admin rights.
    """
    su_name = u"SuperUser"
    become_trusted(request, su_name)
    if su_name not in request.cfg.superuser:
        request.cfg.superuser.append(su_name)
