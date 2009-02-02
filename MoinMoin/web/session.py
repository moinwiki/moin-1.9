# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI session handling

    To provide sessions, the MoinMoin WSGI application interacts with an
    object implementing the `SessionService` API. The interface is quite
    straight forward. For documentation of the expected methods, refer
    to the documentation of `SessionService` in this module.

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
    def get_session(self, request, sid=None):
        """ Return a session object pertaining to the particular request."""
        raise NotImplementedError

    def destroy_session(self, request, session):
        """ Destroy an existing session (make it unusable). """
        raise NotImplementedError

    def finalize(self, request, session):
        """
        If the service needs to do anything to the session and/or request,
        before it is sent back to the client, he can chose to do so here.
        Typical examples would be setting cookies for the client.
        """
        raise NotImplementedError

class FileSessionService(SessionService):
    """
    This sample session service stores session information in a temporary
    directory and identifies the session via a cookie in the request/response
    cycle. It is based on werkzeug's FilesystemSessionStore, that implements
    the whole logic for creating the actual session objects (which are
    inherited from the builtin `dict`)
    """
    def __init__(self, cookie_name='MOIN_SESSION'):
        self.store = FilesystemSessionStore(session_class=MoinSession)
        self.cookie_name = cookie_name

    def get_session(self, request, sid=None):
        if sid is None:
            sid = request.cookies.get(self.cookie_name, None)
        if sid is None:
            session = self.store.new()
        else:
            session = self.store.get(sid)
        return session

    def destroy_session(self, request, session):
        session.clear()
        self.store.delete(session)

    def finalize(self, request, session):
        if request.user.auth_method == 'setuid':
            userobj = request._setuid_real_user
            setuid = request.user.id
        else:
            userobj = request.user
            setuid = None
        logging.debug("finalize userobj = %r, setuid = %r" % (userobj, setuid))
        if userobj and userobj.valid:
            session['user.id'] = userobj.id
            session['user.auth_method'] = userobj.auth_method
            session['user.auth_attribs'] = userobj.auth_attribs
            if setuid:
                session['setuid'] = setuid
            elif 'setuid' in session:
                del session['setuid']
            logging.debug("after auth: storing valid user into session: %r" % userobj.name)
        else:
            if 'user.id' in session:
                self.destroy_session(request, session)

        if session.new:
            cookie_lifetime = request.cfg.cookie_lifetime * 3600
            cookie_expires = time.time() + cookie_lifetime
            if request.cfg.cookie_path:
                cookie_path = request.cfg.cookie_path
            else:
                cookie_path = request.script_root or '/'
            cookie = dump_cookie(self.cookie_name, session.sid,
                                 cookie_lifetime, cookie_expires,
                                 cookie_path, request.cfg.cookie_domain)
            request.headers.add('Set-Cookie', cookie)

        if session.should_save:
            self.store.save(session)

