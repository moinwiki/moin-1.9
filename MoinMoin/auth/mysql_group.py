# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - auth plugin doing a check against MySQL group db

    @copyright: 2006 Nick Phillips,
                2007 MoinMoin:JohannesBerg,
                2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import MySQLdb

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.auth import BaseAuth, CancelLogin, ContinueLogin

class MysqlGroupAuth(BaseAuth):
    """ Authorize via MySQL group DB.

    We require an already-authenticated user_obj and
    check that the user is part of an authorized group.
    """
    def __init__(self, host, user, passwd, dbname, query):
        BaseAuth.__init__(self)
        self.mysql_group_query = query
        self.host = host
        self.user = user
        self.passwd = passwd
        self.dbname = dbname

    def login(self, request, user_obj, **kw):
        _ = request.getText

        logging.debug("got: user_obj=%r" % user_obj)

        if not (user_obj and user_obj.valid):
            # No other method succeeded, so we cannot authorize
            # but maybe some following auth methods can still "fix" that.
            logging.debug("did not get valid user from previous auth method")
            return ContinueLogin(user_obj)

        # Got a valid user object - we can do stuff!
        logging.debug("got valid user (name=%r) from previous auth method" % user_obj.auth_username)

        # XXX Check auth_username for dodgy chars (should be none as it is authenticated, but...)
        # shouldn't really be necessary since execute() quotes them all...

        # OK, now check mysql!
        try:
            m = MySQLdb.connect(host=self.host, user=self.user,
                                passwd=self.passwd, db=self.dbname)
        except:
            logging.exception("authorization failed due to exception when connecting to DB, traceback follows...")
            return CancelLogin(_('Failed to connect to database.'))

        c = m.cursor()
        c.execute(self.mysql_group_query, user_obj.auth_username)
        results = c.fetchall()
        if results:
            # Checked out OK
            logging.debug("got %d results -- authorized!" % len(results))
            return ContinueLogin(user_obj)
        else:
            logging.debug("did not get match from DB -- not authorized")
            return CancelLogin(_("Invalid username or password."))

    # XXX do we really want this? could it be enough to check when they log in?
    # of course then when you change the DB people who are logged in can still do stuff...
    def request(self, request, user_obj, **kw):
        retval = self.login(request, user_obj, **kw)
        return retval.user_obj, retval.continue_flag

