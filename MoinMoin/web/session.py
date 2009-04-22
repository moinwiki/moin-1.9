# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI session handling

    To provide sessions, the MoinMoin WSGI application interacts with an
    object implementing the `SessionService` API. The interface is quite
    straight forward. For documentation of the expected methods, refer
    to the documentation of `SessionService` in this module.

    @copyright: 2008 MoinMoin:FlorianKrupicka,
                2009 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import time

from werkzeug.contrib.sessions import FilesystemSessionStore, Session

from MoinMoin.util import filesys

from MoinMoin import log
logging = log.getLogger(__name__)

class MoinSession(Session):
    """ Compatibility interface to Werkzeug-sessions for old Moin-code. """
    is_new = property(lambda s: s.new)

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

def _get_session_lifetime(request, userobj):
    """ Get session lifetime for the user object userobj
    Cookie lifetime in hours, can be fractional. First tuple element is for anonymous sessions,
    second tuple element is for logged-in sessions. For anonymous sessions,
    t=0 means that they are disabled, t>0 means that many hours.
    For logged-in sessions, t>0 means that many hours,
    or forever if user checked 'remember_me', t<0 means -t hours and
    ignore user 'remember_me' setting - you usually don't want to use t=0, it disables logged-in sessions."""
    lifetime = int(float(request.cfg.cookie_lifetime[userobj and userobj.valid]) * 3600)
    forever = 10 * 365 * 24 * 3600 # 10 years

    if userobj and userobj.valid and userobj.remember_me and lifetime > 0:
        return forever
    return abs(lifetime)

class FileSessionService(SessionService):
    """
    This sample session service stores session information in a temporary
    directory and identifies the session via a cookie in the request/response
    cycle. It is based on werkzeug's FilesystemSessionStore, that implements
    the whole logic for creating the actual session objects (which are
    inherited from the builtin `dict`)
    """
    def __init__(self, cookie_name='MOIN_SESSION'):
        self.cookie_name = cookie_name
        self.store = None

    def _store_get(self, request):
        if self.store is None:
            path = request.cfg.session_dir
            try:
                filesys.mkdir(path)
            except OSError:
                pass
            self.store = FilesystemSessionStore(path=path, filename_template='%s', session_class=MoinSession)
        return self.store

    def get_session(self, request, sid=None):
        if sid is None:
            sid = request.cookies.get(self.cookie_name, None)
        store = self._store_get(request)
        if sid is None:
            session = store.new()
        else:
            session = store.get(sid)
        return session

    def destroy_session(self, request, session):
        session.clear()
        store = self._store_get(request)
        store.delete(session)

    def finalize(self, request, session):
        if request.user.auth_method == 'setuid':
            userobj = request._setuid_real_user
            setuid = request.user.id
        else:
            userobj = request.user
            setuid = None
        logging.debug("finalize userobj = %r, setuid = %r" % (userobj, setuid))
        cfg = request.cfg
        cookie_path = cfg.cookie_path or request.script_root or '/'
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
            logging.debug("after auth: user is invalid")
            if 'user.id' in session:
                logging.debug("after auth: destroying session: %r" % session)
                self.destroy_session(request, session)
                logging.debug("after auth: deleting session cookie!")
                request.delete_cookie(self.cookie_name, path=cookie_path, domain=cfg.cookie_domain)

        cookie_lifetime = _get_session_lifetime(request, userobj)
        if cookie_lifetime:
            cookie_expires = time.time() + cookie_lifetime
            # a secure cookie is not transmitted over unsecure connections:
            cookie_secure = (cfg.cookie_secure or  # True means: force secure cookies
                             cfg.cookie_secure is None and request.is_secure)  # None means: https -> secure cookie
            logging.debug("user: %r, setting session cookie: %r" % (userobj, session.sid))
            request.set_cookie(self.cookie_name, session.sid,
                               max_age=cookie_lifetime, expires=cookie_expires,
                                path=cookie_path, domain=cfg.cookie_domain,
                               secure=cookie_secure, httponly=cfg.cookie_httponly)

            if session.should_save:
                store = self._store_get(request)
                logging.debug("saving session: %r" % session)
                store.save(session)

