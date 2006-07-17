# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - auth plugin doing a check against MySQL group db

    @copyright: 2006 by Nick Phillips
    @license: GNU GPL, see COPYING for details.
"""

import MySQLdb

def mysql_group(request, **kw):
    """ Authorize via MySQL group DB.
    
    We require an already-authenticated user_obj.
    We don't worry about the type of request (login, logout, neither).
    We just check user is part of authorized group.
    """

    username = kw.get('name')
#    login = kw.get('login')
#    logout = kw.get('logout')
    user_obj = kw.get('user_obj')

    cfg = request.cfg
    verbose = False

    if hasattr(cfg, 'mysql_group_verbose'):
        verbose = cfg.mysql_group_verbose

    if verbose: request.log("auth.mysql_group: name=%s user_obj=%r" % (username, user_obj))

    # Has any other method successfully authenticated?
    if user_obj is not None and user_obj.valid:
        # Yes - we can do stuff!
        if verbose: request.log("mysql_group got valid user from previous auth method, trying authz...")
        if verbose: request.log("mysql_group got auth_username %s." % user_obj.auth_username)

        # XXX Check auth_username for dodgy chars (should be none as it is authenticated, but...)

        # OK, now check mysql!
        try:
            m = MySQLdb.connect(host=cfg.mysql_group_dbhost,
                                user=cfg.mysql_group_dbuser,
                                passwd=cfg.mysql_group_dbpass,
                                db=cfg.mysql_group_dbname,
                                )
        except:
            import sys
            import traceback
            info = sys.exc_info()
            request.log("mysql_group: authorization failed due to exception connecting to DB, traceback follows...")
            request.log(''.join(traceback.format_exception(*info)))
            return None, False

        c = m.cursor()
        c.execute(cfg.mysql_group_query, user_obj.auth_username)
        results = c.fetchall()
        if results:
            # Checked out OK
            if verbose: request.log("mysql_group got %d results -- authorized!" % len(results))
            return user_obj, True # we make continuing possible, e.g. for smbmount
        else:
            if verbose: request.log("mysql_group did not get match from DB -- not authorized")
            return None, False
    else:
        # No other method succeeded, so we cannot authorize -- must fail
        if verbose: request.log("mysql_group did not get valid user from previous auth method, cannot authorize")
        return None, False

