"""
    MoinMoin - session handling

    Session handling in MoinMoin is done mostly by the request
    with help from a SessionHandler instance (see below.)


    @copyright: 2007 MoinMoin:JohannesBerg,
                2008 MoinMoin:ThomasWaldmann

    @license: GNU GPL, see COPYING for details.
"""

import Cookie

from MoinMoin import log
logging = log.getLogger(__name__)

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
            logging.debug("loaded session data from cache entry: %r" % self._data)
            if self['expires'] <= time.time():
                logging.debug("session expired, removing session cache entry")
                self._ce.remove()
                self._data = {'expires': 0}
        except caching.CacheError:
            self._data = {'expires': 0}

    def __setitem__(self, name, value):
        self._data[name] = value
        if len(self._data) > 1 and self['expires'] > time.time():
            logging.debug("storing %r:%r item into session cache entry" % (name, value))
            self._ce.update(self._data)

    def __getitem__(self, name):
        return self._data[name]

    def __contains__(self, name):
        return name in self._data

    def __delitem__(self, name):
        old_value = self._data[name]
        del self._data[name]
        if len(self._data) <= 1:
            self._ce.remove()
        elif self['expires'] > time.time():
            logging.debug("removing %r:%r item from session cache entry" % (name, old_value))
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
        removed_count = 0
        for name in cachelist:
            entry = caching.CacheEntry(request, 'session', name, 'farm',
                                       use_pickle=True)
            try:
                data = entry.content()
                if 'expires' in data and data['expires'] < tnow:
                    entry.remove()
                    removed_count += 1
            except caching.CacheError:
                pass
        logging.debug("removed %d expired sessions while performing session cache cleanup" % removed_count)
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




class SessionIDHandler:
    """
        MoinMoin session ID handling

        Instances of this class are used by the session handling code
        to set/get the persistent ID that is used to identify the session
        which is usually stored in a cookie.
    """
    _SESSION_NAME_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789_'
    _SESSION_NAME_LEN = 32

    def __init__(self):
        """
            Initialise the session ID handler.
        """
        pass

    def get(self, request):
        """
            Return the persistent ID for this request.

            @param request: the request instance
        """
        raise NotImplementedError

    def set(self, request, session_id, expires):
        """
            Set a persistent ID for the request to be returned by the
            user agent.

            @param request: the request instance
            @param session_id: the ID for this session
            @param expires: expiry date/time in unix seconds (cf. time.time())
        """
        raise NotImplementedError

    def generate_new_id(self, request):
        """
            Generate a new unique ID.

            @param request: the request instance
        """
        return random_string(self._SESSION_NAME_LEN, self._SESSION_NAME_CHARS)



class MoinCookieSessionIDHandler(SessionIDHandler):
    def __init__(self, cookie_name='MOIN_SESSION'):
        SessionIDHandler.__init__(self)
        self.cookie_name = cookie_name

    def _make_cookie(self, request, cookie_name, cookie_string, maxage, expires, http_only=False):
        """ create an appropriate cookie """
        cookie = Cookie.SimpleCookie()
        cfg = request.cfg
        cookie[cookie_name] = cookie_string
        if http_only:
            try:
                # needs python 2.6 httponly Cookie support:
                cookie[cookie_name]['httponly'] = True
            except Cookie.CookieError:
                pass
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
        # a secure cookie is not transmitted over unsecure connections:
        if (cfg.cookie_secure or  # True means: force secure cookies
            cfg.cookie_secure is None and request.is_ssl):  # None means: https -> secure cookie
            cookie[cookie_name]['secure'] = True
        return cookie.output()

    def _set_cookie(self, request, cookie_string, expires, http_only=False):
        """ Set cookie, raw helper. """
        lifetime = int(expires - time.time())
        cookie = self._make_cookie(request, self.cookie_name, cookie_string,
                                   lifetime, expires, http_only)
        # Set cookie
        request.setHttpHeader(cookie)
        # IMPORTANT: Prevent caching of current page and cookie
        request.disableHttpCaching()

    def set(self, request, session_name, expires):
        """ Set moin_session cookie """
        self._set_cookie(request, session_name, expires, http_only=False) # TODO: cfg.cookie_httponly as in 1.9
        logging.debug("setting cookie with session_name %r, expiry %r" % (session_name, expires))

    def get(self, request):
        session_name = None
        if request.cookie and self.cookie_name in request.cookie:
            session_name = request.cookie[self.cookie_name].value
            session_name = ''.join([c for c in session_name
                                    if c in self._SESSION_NAME_CHARS])
            session_name = session_name[:self._SESSION_NAME_LEN]
            logging.debug("got cookie with session_name %r" % session_name)
        return session_name


def _get_anon_session_lifetime(request):
    if request.cfg.anonymous_session_lifetime:
        return request.cfg.anonymous_session_lifetime * 3600
    return 0

def _get_session_lifetime(request, user_obj):
    """ Get session lifetime for the user object user_obj """
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

    def start(self, request, session_id_handler):
        user_obj = None
        session_name = session_id_handler.get(request)
        if session_name:
            logging.debug("starting session (reusing session_name %r)" % session_name)
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
                store = not (not request.cfg.anonymous_session_lifetime)
                sessiondata.is_stored = store
        else:
            session_name = session_id_handler.generate_new_id(request)
            logging.debug("starting session (new session_name %r)" % session_name)
            store = not (not request.cfg.anonymous_session_lifetime)
            sessiondata = self.dataclass(request, session_name)
            sessiondata.is_new = True
            sessiondata.is_stored = store
            request.session = sessiondata
        logging.debug("session started for user %r" % user_obj)
        return user_obj

    def after_auth(self, request, session_id_handler, user_obj):
        session = request.session
        if user_obj and user_obj.valid:
            if 'user.id' in session and session['user.id'] != user_obj.id:
                session.delete()
            session['user.id'] = user_obj.id
            session['user.auth_method'] = user_obj.auth_method
            session['user.auth_attribs'] = user_obj.auth_attribs
            lifetime = _get_session_lifetime(request, user_obj)
            expires = time.time() + lifetime
            session_id_handler.set(request, session.name, expires)
            request.session.set_expiry(expires)
            logging.debug("after auth: storing valid user into session: %r" % user_obj.name)
        else:
            if 'user.id' in session:
                session.delete()
            lifetime = _get_anon_session_lifetime(request)
            if lifetime:
                expires = time.time() + lifetime
                session_id_handler.set(request, session.name, expires)
                request.session.set_expiry(expires)
                logging.debug("after auth: no valid user, anon session: %r" % session.name)
            else:
                session.delete()
                logging.debug("after auth: no valid user, no anon session")

    def finish(self, request, session_id_handler, user_obj):
        # every once a while, clean up deleted sessions:
        if random.randint(0, 999) == 0:
            self.dataclass.cleanup(request)
