"""
    MoinMoin - session handling

    Session handling in MoinMoin is done mostly by the request
    with help from a SessionHandler instance (see below.)


    @copyright: 2007      MoinMoin:JohannesBerg

    @license: GNU GPL, see COPYING for details.
"""

import Cookie
from MoinMoin import caching
from MoinMoin.user import User
from MoinMoin.util import random_string
import time, random

class SessionData(object):
    """
        MoinMoin session data base class

        An object of this class must be assigned to
        request.session by the SessionHandler's start
        method.

        Instances conform to the dict protocol (__setitem__, __getitem__,
        __contains__, __delitem__, get) and have the additional properties
        is_stored and is_new.
    """
    def __init__(self, request):
        self.is_stored = False
        self.is_new = True
        self.request = request

    def __setitem__(self, name, value):
        raise NotImplementedError

    def __getitem__(self, name):
        raise NotImplementedError

    def __contains__(self, name):
        raise NotImplementedError

    def __delitem__(self, name):
        raise NotImplementedError

    def get(self, name, default=None):
        raise NotImplementedError


class DefaultSessionData(SessionData):
    """ DefaultSessionData -- session data for DefaultSessionHandler

    If you wish to override just the session storage then you can
    inherit from this class, implement all methods and assign the
    class to the dataclass keyword parameter to the DefaultSessionHandler
    constructor.

    Newly created objects should have be marked as expiring right away
    until set_expiry() is called.
    """
    def __init__(self, request, name):
        """create session object

        @param request: the request
        @param name: the session name
        """
        SessionData.__init__(self, request)
        self.name = name

    def set_expiry(self, expires):
        """reset expiry for this session object"""
        raise NotImplementedError

    def delete(self):
        """clear session data and remove from it storage"""
        raise NotImplementedError

    def cleanup(cls, request):
        """clean up expired sessions"""
        raise NotImplementedError
    cleanup = classmethod(cleanup)

class CacheSessionData(DefaultSessionData):
    """ SessionData -- store data for a session

    This stores session data in memory and also maintains a cache of it on
    disk, so the same data will be loaded from disk cache in the next request
    of the same session.

    Once in a while, expired session's cache files will be automatically cleaned up.
    """
    def __init__(self, request, name):
        DefaultSessionData.__init__(self, request, name)

        # we can use farm scope since the session name is totally random
        # this means that the session is kept over multiple wikis in a farm
        # when they share user_dir and cookies
        self._ce = caching.CacheEntry(request, 'session', name, 'farm',
                                      use_pickle=True)
        try:
            self._data = self._ce.content()
            if self['expires'] <= time.time():
                self._ce.remove()
                self._data = {'expires': 0}
        except caching.CacheError:
            self._data = {'expires': 0}

    def __setitem__(self, name, value):
        self._data[name] = value
        if len(self._data) > 1 and self['expires'] > time.time():
            self._ce.update(self._data)

    def __getitem__(self, name):
        return self._data[name]

    def __contains__(self, name):
        return name in self._data

    def __delitem__(self, name):
        del self._data[name]
        if len(self._data) <= 1:
            self._ce.remove()
        elif self['expires'] > time.time():
            self._ce.update(self._data)

    def get(self, name, default=None):
        return self._data.get(name, default)

    def set_expiry(self, expires):
        # Set 'expires' an hour later than it should actually expire.
        # That way, the expiry code will delete the item an hour later
        # than it has actually expired, but that is acceptable and we
        # don't need to update the file all the time
        if expires and self['expires'] < expires:
            self['expires'] = expires + 3600

    def delete(self):
        try:
            self._ce.remove()
        except caching.CacheError:
            pass
        self._data = {'expires': 0}

    def cleanup(cls, request):
        cachelist = caching.get_cache_list(request, 'session', 'farm')
        tnow = time.time()
        for name in cachelist:
            entry = caching.CacheEntry(request, 'session', name, 'farm',
                                       use_pickle=True)
            try:
                data = entry.content()
                if 'expires' in data and data['expires'] < tnow:
                    entry.remove()
            except caching.CacheError:
                pass
    cleanup = classmethod(cleanup)


class SessionHandler(object):
    """
        MoinMoin session handler base class

        SessionHandler is an abstract method defining the interface
        to a session handler object.

        Session handling in MoinMoin works as follows:

        When a request is received, first the cookie is read into a
        Cookie.SimpleCookie instance, this is passed to the selected
        session handler's (cfg.session_handler) start method (see below)
        which must return a MoinMoin.user.User instance (or None). The
        session handler is also responsible for string the user object's
        auth_method and auth_attribs fields across sessions as those are
        not saved to the user file.

        Then, all authentication methods are called with this user object,
        they can modify it or return a different one.

        After they have changed the user object suitably, the session
        handler's after_auth method is invoked to set the cookie.

        Then, the request is executed and finally the session handler's
        finish method is invoked.
    """
    def __init__(self):
        """
           Session handler initialisation

           Only provided for future compatibility.
        """
        pass

    def start(self, request, cookie):
        """
           Session handler start

           Invoked very early during request handling to preload
           a user object from the session (if any.)
           This method must also assign to request.session an object
           derived from SessionDataInterface.

           @param request: the request instance
           @param cookie: a Cookie.SimpleCookie with the request cookie
           @return: a MoinMoin.user.User instance or None
        """
        raise NotImplementedError

    def after_auth(self, request, cookie, user_obj):
        """
           Session handler auth chain callback

           Invoked after all auth items have run (or multistage was
           requested by one), but before the request is actually
           handled and output is made. Should set the cookie.

           @param request: the request instance
           @param cookie: a Cookie.SimpleCookie with the request cookie
           @param user_obj: the user object returned from the auth methods
                            (or None)
        """
        raise NotImplementedError

    def finish(self, request, cookie, user_obj):
        """
           Session handler request finish callback

           Invoked after the request is completely finished.

           @param request: the request instance
           @param cookie: a Cookie.SimpleCookie with the request cookie
           @param user_obj: the user object that was used in this request
        """
        raise NotImplementedError

_MOIN_SESSION = 'MOIN_SESSION'

_SESSION_NAME_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789_-'
_SESSION_NAME_LEN = 32


def _make_cookie(request, cookie_name, cookie_string, maxage, expires):
    """ create an appropriate cookie """
    cookie = Cookie.SimpleCookie()
    cfg = request.cfg
    cookie[cookie_name] = cookie_string
    cookie[cookie_name]['max-age'] = maxage
    if cfg.cookie_domain:
        cookie[cookie_name]['domain'] = cfg.cookie_domain
    if cfg.cookie_path:
        cookie[cookie_name]['path'] = cfg.cookie_path
    else:
        path = request.getScriptname()
        if not path:
            path = '/'
        cookie[cookie_name]['path'] = path
    # Set expires for older clients
    cookie[cookie_name]['expires'] = request.httpDate(when=expires, rfc='850')
    return cookie.output()


def _get_cookie_lifetime(request, user_obj):
    """ Get cookie lifetime for the user object user_obj """
    lifetime = int(request.cfg.cookie_lifetime) * 3600
    forever = 10 * 365 * 24 * 3600 # 10 years
    if not lifetime:
        return forever
    elif lifetime > 0:
        if user_obj.remember_me:
            return forever
        return lifetime
    elif lifetime < 0:
        return -lifetime
    return lifetime


def _set_cookie(request, cookie_string, maxage, expires):
    """ Set cookie, raw helper. """
    cookie = _make_cookie(request, _MOIN_SESSION, cookie_string,
                          maxage, expires)
    # Set cookie
    request.setHttpHeader(cookie)
    # IMPORTANT: Prevent caching of current page and cookie
    request.disableHttpCaching()


def _set_session_cookie(request, session_name, lifetime):
    """ Set moin_session cookie """
    expires = time.time() + lifetime
    request.session.set_expiry(expires)
    _set_cookie(request, session_name, lifetime, expires)


def _get_session_name(cookie):
    session_name = None
    if _MOIN_SESSION in cookie:
        session_name = cookie[_MOIN_SESSION].value
        session_name = ''.join([c for c in session_name
                                if c in _SESSION_NAME_CHARS])
        session_name = session_name[:_SESSION_NAME_LEN]
    return session_name


def _set_anon_cookie(request, session_name):
    if hasattr(request.cfg, 'anonymous_cookie_lifetime'):
        lifetime = request.cfg.anonymous_cookie_lifetime * 3600
        _set_session_cookie(request, session_name, lifetime)


class DefaultSessionHandler(SessionHandler):
    """MoinMoin default session handler

    This session handler uses the MOIN_SESSION cookie and a configurable
    session data class.
    """
    def __init__(self, dataclass=CacheSessionData):
        """DefaultSessionHandler constructor

        @param dataclass: class derived from DefaultSessionData or a callable
                          that takes parameters (request, name, expires)
                          and returns a DefaultSessionData instance.
        """
        SessionHandler.__init__(self)
        self.dataclass = dataclass

    def start(self, request, cookie):
        user_obj = None
        session_name = _get_session_name(cookie)
        if session_name:
            sessiondata = self.dataclass(request, session_name)
            sessiondata.is_new = False
            sessiondata.is_stored = True
            request.session = sessiondata
            if 'user.id' in sessiondata:
                uid = sessiondata['user.id']
                method = sessiondata['user.auth_method']
                attribs = sessiondata['user.auth_attribs']
                # Only allow valid methods that are still in the auth list.
                # This is necessary to kick out clients who authenticated in
                # the past with a method that was removed from the auth list!
                if method:
                    for auth in request.cfg.auth:
                        if auth.name == method:
                            user_obj = User(request, id=uid,
                                            auth_method=method,
                                            auth_attribs=attribs)
                            if user_obj:
                                sessiondata.is_stored = True
            else:
                store = hasattr(request.cfg, 'anonymous_cookie_lifetime')
                sessiondata.is_stored = store
        else:
            session_name = random_string(_SESSION_NAME_LEN,
                                         _SESSION_NAME_CHARS)
            store = hasattr(request.cfg, 'anonymous_cookie_lifetime')
            sessiondata = self.dataclass(request, session_name)
            sessiondata.is_new = True
            sessiondata.is_stored = store
            request.session = sessiondata
        return user_obj

    def after_auth(self, request, cookie, user_obj):
        session = request.session
        if user_obj and user_obj.valid:
            session['user.id'] = user_obj.id
            session['user.auth_method'] = user_obj.auth_method
            session['user.auth_attribs'] = user_obj.auth_attribs
            lifetime = _get_cookie_lifetime(request, user_obj)
            _set_session_cookie(request, session.name, lifetime)
        else:
            if 'user.id' in session:
                session.delete()
            _set_anon_cookie(request, session.name)

    def finish(self, request, cookie, user_obj):
        # every once a while, clean up deleted sessions:
        if random.randint(0, 999) == 0:
            self.dataclass.cleanup(request)
