# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI session handling

    Session handling

    @copyright: 2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
import time

from werkzeug.utils import dump_cookie
from werkzeug.contrib.sessions import FilesystemSessionStore, Session

from MoinMoin import caching

from MoinMoin import log
logging = log.getLogger(__name__)

class MoinSession(Session):
    """ Compatibility interface to Werkzeug-sessions for old Moin-code. """
    is_new = property(lambda s: s.new)
    is_stored = property(lambda s: True)

class SessionService(object):
    """
    A session service returns a session object given a request object and
    provides services like persisting sessions and cleaning up occasionally.
    """
    def get_session(self, request):
        """ Return a session object pertaining to the particular request."""
        raise NotImplementedError

    def destroy_session(self, request, session):
        """ Destroy an existing session (make it unusable). """
        raise NotImplementedError

    def finalize(self, request, session):
        """
        Do final modifications to the request and/or session before sending
        headers and body to the cliebt.
        """
        raise NotImplementedError

class FileSessionService(SessionService):
    """
    This sample session service stores session information in a temporary
    directory and identifis the session via a cookie in the request/response
    cycle.
    """

    def __init__(self, cookie_name='MOIN_SESSION'):
        self.store = FilesystemSessionStore(session_class=MoinSession)
        self.cookie_name = cookie_name

    def get_session(self, request):
        sid = request.cookies.get(self.cookie_name, None)
        if sid is None:
            session = self.store.new()
        else:
            session = self.store.get(sid)
        return session

    def destroy_session(self, request, session):
        session.clear()
        self.store.delete(session)
        session.modified = session.new = False

    def finalize(self, request, session):
        userobj = request.user
        if userobj and userobj.valid:
            if 'user.id' in session and session['user.id'] != userobj.id:
                request.cfg.session_service.delete(session)
            session['user.id'] = userobj.id
            session['user.auth_method'] = userobj.auth_method
            session['user.auth_attribs'] = userobj.auth_attribs
            logging.debug("after auth: storing valid user into session: %r" % userobj.name)
        else:
            if 'user.id' in session:
                self.destroy_session(request, session)

        if session.should_save:
            self.store.save(session)

        if session.new:
            cookie_lifetime = request.cfg.cookie_lifetime * 3600
            cookie_expires = time.time() + cookie_lifetime
            cookie = dump_cookie(self.cookie_name, session.sid,
                                 cookie_lifetime, cookie_expires,
                                 request.cfg.cookie_domain,
                                 request.cfg.cookie_path)
            request.headers.add('Set-Cookie', cookie)
