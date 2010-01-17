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
import time, os

from werkzeug.contrib.sessions import FilesystemSessionStore, Session

from MoinMoin.util import filesys

from MoinMoin import log
logging = log.getLogger(__name__)

class MoinSession(Session):
    """ Compatibility interface to Werkzeug-sessions for old Moin-code. """
    is_new = property(lambda s: s.new)

    def __repr__(self):
        # TODO: try to get this into werkzeug codebase
        return '<%s %s %s%s>' % (
            self.__class__.__name__,
            self.sid, # we want to see sid
            dict.__repr__(self),
            self.should_save and '*' or ''
        )


class FixedFilesystemSessionStore(FilesystemSessionStore):
    """
    Fix buggy implementation of .get() in werkzeug <= 0.5:

    If you try to get(somesid) and the file with the contents of sid storage
    does not exist or is troublesome somehow, it will create a new session
    with a new sid in werkzeug 0.5 original implementation.

    But we do not want to store a session file for new and empty sessions,
    but rather wait for the 2nd request and see whether the user agent sends
    the cookie back to us. If it doesn't support cookies, we don't want to
    create one new session file per request. If it does support cookies, we
    need to use .get() with the sid although there was no session file stored
    for that sid in the first request.

    TODO: try to get it into werkzeug codebase and remove this class after
          we REQUIRE a werkzeug release > 0.5 that has it.
    """
    def get(self, sid):
        from cPickle import load
        if not self.is_valid_key(sid):
            return self.new()
        fn = self.get_session_filename(sid)
        f = None
        try:
            try:
                f = open(fn, 'rb')
                data = load(f)
            except (IOError, EOFError, KeyError): # XXX check completeness/correctness
                # Note: we do NOT generate a new sid in case of trouble with session *contents*
                # IOError: [Errno 2] No such file or directory
                # IOError: [Errno 13] Permission denied (we will notice permission problems when writing)
                # EOFError: when trying to load("") - no contents
                # KeyError: when trying to load("xxx") - crap contents
                data = {}
        finally:
            if f:
                f.close()
        return self.session_class(data, sid, False)

    """
    Adds functionality missing in werkzeug 0.5: getting a list of all SIDs,
    so that purging sessions can be implemented.
    """
    def get_all_sids(self):
        """
        return a list of all session ids (sids)
        """
        import re
        regex = re.compile(re.escape(self.filename_template).replace(r'\%s', r'(.+)'))
        sids = []
        for fn in os.listdir(self.path):
            m = regex.match(fn)
            if m:
                sids.append(m.group(1))
        return sids


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

    def get_all_session_ids(self, request):
        """
        Return a list of all session ids known to the SessionService.
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

def get_cookie_name(request, name, usage, software='MOIN'):
    """
    Determine the full cookie name for some software (usually 'MOIN') using
    it for some usage (e.g. 'SESSION') for some wiki (or group of wikis)
    determined by name.

    Note:
    -----
    We do not use the path=... information in the cookie any more, because it can
    easily cause confusion if there are multiple cookies with same name, but
    different pathes (like e.g. / and /foo).

    Instead of using the cookie path, we use differently named cookies, so we get
    the right cookie no matter at what URL the wiki currently is "mounted".

    If name is None, we use some URL components to make up some name.
    For example the cookie name for the default desktop wiki: MOIN_SESSION_8080_ROOT

    If name is siteidmagic, we just use cfg.siteid, which is unique within a wiki farm
    created by a single farmconfig. If you only run ONE(!) wikiconfig wiki, it
    is also unique, of course, but not if you run multiple wikiconfig wikis under
    same domain.

    If name is not None (and not 'siteidmagic'), we just use the given name (you
    want to use that to share stuff between several wikis - just give same name
    and it will use the same cookie. same thing if you don't want to share, just
    give a different name then [e.g. if cfg.siteid or 'siteidmagic' doesn't work
    for you]).

    Moving a wiki to a different URL will break all sessions. Exchanging URLs
    of wikis might lead to confusion (requiring the client to purge the cookies).
    """
    if name is None:
        url_components = [
            # cookies do not store the port, thus we add it to the cookie name:
            request.environ['SERVER_PORT'],
            # we always store path=/ into cookie, thus we add the path to the name:
            ('ROOT' + request.script_root).replace('/', '_'),
        ]
        name = '_'.join(url_components)

    elif name is 'siteidmagic':
        name = request.cfg.siteid  # == config name, unique per farm

    return "%s_%s_%s" % (software, usage, name)


class FileSessionService(SessionService):
    """
    This sample session service stores session information in a temporary
    directory and identifies the session via a cookie in the request/response
    cycle. It is based on werkzeug's FilesystemSessionStore, that implements
    the whole logic for creating the actual session objects (which are
    inherited from the builtin `dict`)
    """
    def __init__(self, cookie_usage='SESSION'):
        self.cookie_usage = cookie_usage

    def _store_get(self, request):
        path = request.cfg.session_dir
        try:
            filesys.mkdir(path)
        except OSError:
            pass
        return FixedFilesystemSessionStore(path=path, filename_template='%s', session_class=MoinSession)

    def get_session(self, request, sid=None):
        if sid is None:
            cookie_name = get_cookie_name(request, name=request.cfg.cookie_name, usage=self.cookie_usage)
            sid = request.cookies.get(cookie_name, None)
        logging.debug("get_session for sid %r" % sid)
        store = self._store_get(request)
        if sid is None:
            session = store.new()
        else:
            session = store.get(str(sid))
        logging.debug("get_session returns session %r" % session)
        return session

    def get_all_session_ids(self, request):
        store = self._store_get(request)
        return store.get_all_sids()

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
        # we use different cookie names for different wikis:
        cookie_name = get_cookie_name(request, name=request.cfg.cookie_name, usage=self.cookie_usage)
        # we always use path='/' except if explicitly overridden by configuration,
        # which is usually not needed and not recommended:
        cookie_path = cfg.cookie_path or '/'
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
                request.delete_cookie(cookie_name, path=cookie_path, domain=cfg.cookie_domain)

        cookie_lifetime = _get_session_lifetime(request, userobj)
        if cookie_lifetime:
            cookie_expires = time.time() + cookie_lifetime
            # a secure cookie is not transmitted over unsecure connections:
            cookie_secure = (cfg.cookie_secure or  # True means: force secure cookies
                             cfg.cookie_secure is None and request.is_secure)  # None means: https -> secure cookie
            logging.debug("user: %r, setting session cookie: %r" % (userobj, session.sid))
            request.set_cookie(cookie_name, session.sid,
                               max_age=cookie_lifetime, expires=cookie_expires,
                               path=cookie_path, domain=cfg.cookie_domain,
                               secure=cookie_secure, httponly=cfg.cookie_httponly)

            if ((not userobj.valid and not session.new  # anon users with a cookie (not first request)
                 or
                 userobj.valid) # logged-in users, even if THIS was the first request (no cookie yet)
                                # XXX if UA doesn't support cookies, this creates 1 session file per request
                and
                session.modified): # only if we really have something to save
                # add some info about expiry to the sessions, so we can purge them:
                session['expires'] = cookie_expires
                # note: currently, every request of a logged-in user will save
                # the session, even when always requesting same page.
                # No big deal, as we store the trail into session and that
                # likely changes with every request anyway.
                store = self._store_get(request)
                logging.debug("saving session: %r" % session)
                store.save(session)

