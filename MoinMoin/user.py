# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User Accounts

    This module contains functions to access user accounts (list all users, get
    some specific user). User instances are used to access the user profile of
    some specific user (name, password, email, bookmark, trail, settings, ...).

    Some related code is in the userform and userprefs modules.

    TODO:
    * code is a mixture of highlevel user stuff and lowlevel storage functions,
      this has to get separated into:
      * user object highlevel stuff
      * storage code

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2003-2013 MoinMoin:ThomasWaldmann,
                2010 Michael Foetsch <foetsch@yahoo.com>
    @license: GNU GPL, see COPYING for details.
"""

import os, time, codecs, base64
from copy import deepcopy
import md5crypt

try:
    import crypt
except ImportError:
    crypt = None

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.support.python_compatibility import hash_new, hmac_new

from MoinMoin import config, caching, wikiutil, i18n, events
from werkzeug.security import safe_str_cmp as safe_str_equal
from MoinMoin.util import timefuncs, random_string
from MoinMoin.wikiutil import url_quote_plus

# for efficient lookup <attr> -> userid, we keep an index of this in the cache.
# the attribute names in here should be uniquely identifying a user.
CACHED_USER_ATTRS = ['name', 'email', 'jid', 'openids', ]


def getUserList(request):
    """ Get a list of all (numerical) user IDs.

    @param request: current request
    @rtype: list
    @return: all user IDs
    """
    import re
    user_re = re.compile(r'^\d+\.\d+(\.\d+)?$')
    files = os.listdir(request.cfg.user_dir)
    userlist = [f for f in files if user_re.match(f)]
    return userlist

def get_by_filter(request, filter_func):
    """ Searches for a user with a given filter function

    Be careful: SLOW for big wikis, rather use _getUserIdByKey & related.
    """
    for uid in getUserList(request):
        theuser = User(request, uid)
        if filter_func(theuser):
            return theuser

def get_by_email_address(request, email_address):
    """ Searches for an user with a particular e-mail address and returns it. """
    uid = _getUserIdByKey(request, 'email', email_address, case=False)
    if uid is not None:
        return User(request, uid)

def get_by_jabber_id(request, jabber_id):
    """ Searches for an user with a perticular jabber id and returns it. """
    uid = _getUserIdByKey(request, 'jid', jabber_id, case=False)
    if uid is not None:
        return User(request, uid)

def _getUserIdByKey(request, key, search, case=True):
    """ Get the user ID for a specified key/value pair.

    This method must only be called for keys that are
    guaranteed to be unique.

    @param key: the key to look in
    @param search: the value to look for
    @param case: do a case-sensitive lookup?
    @return the corresponding user ID or None
    """
    if key not in CACHED_USER_ATTRS:
        raise ValueError("unsupported key, must be in CACHED_USER_ATTRS")
    if not search:
        return None
    cfg_cache_attr = key + "2id"
    if not case:
        cfg_cache_attr += "_lower"
        search = search.lower()
    cfg = request.cfg
    try:
        attr2id = getattr(cfg.cache, cfg_cache_attr)
        from_disk = False
    except AttributeError:
        # no in-memory cache there - initialize it / load it from disk
        loadLookupCaches(request)
        attr2id = getattr(cfg.cache, cfg_cache_attr)
        from_disk = True  # we just loaded the stuff from disk
    uid = attr2id.get(search, None)
    if uid is None and not from_disk:
        # we do not have the entry we searched for.
        # we didn't find it in some in-memory cache, try refreshing these from disk
        loadLookupCaches(request)
        attr2id = getattr(cfg.cache, cfg_cache_attr)
        from_disk = True  # we just loaded the stuff from disk
        uid = attr2id.get(search, None)
    if uid is None:
        # we do not have the entry we searched for.
        # we don't have it in the on-disk cache, cache MISS.
        # could be because:
        # a) ok: we have no such search value in the profiles
        # b) fault: the cache is incoherent with the profiles
        # c) fault: reading the cache from disk failed, due to an error
        # d) ok: same as c), but just because no ondisk cache has been built yet
        rebuildLookupCaches(request)  # XXX expensive
        attr2id = getattr(cfg.cache, cfg_cache_attr)
        uid = attr2id.get(search, None)
    return uid


def setMemoryLookupCaches(request, cache):
    """set the in-memory cache from the given cache contents

    @param request: the request object
    @param cache: either a dict of attrname -> attrcache to set the in-memory cache,
                  or None to delete the in-memory cache.
    """
    for attrname in CACHED_USER_ATTRS:
        if cache is None:
            try:
                delattr(request.cfg.cache, attrname + "2id")
            except:
                pass
            try:
                delattr(request.cfg.cache, attrname + "2id_lower")
            except:
                pass
        else:
            setattr(request.cfg.cache, attrname + "2id", cache[attrname])
            setattr(request.cfg.cache, attrname + "2id_lower", cache[attrname + "_lower"])


def loadLookupCaches(request):
    """load lookup cache contents into memory: cfg.cache.XXX2id"""
    scope, arena, cachekey = 'userdir', 'users', 'lookup'
    diskcache = caching.CacheEntry(request, arena, cachekey, scope=scope, use_pickle=True)
    try:
        cache = diskcache.content()
    except caching.CacheError:
        cache = {}
        for attrname in CACHED_USER_ATTRS:
            cache[attrname] = {}
    cache_with_lowercase = addLowerCaseKeys(cache)
    setMemoryLookupCaches(request, cache_with_lowercase)


def rebuildLookupCaches(request):
    """complete attrs -> userid lookup cache rebuild"""
    # as there may be thousands of users and reading all profiles is
    # expensive, we just have 1 lookup cache for all interesting user attrs,
    # so we only need to read all profiles ONCE to build the cache.
    scope, arena, key = 'userdir', 'users', 'lookup'
    diskcache = caching.CacheEntry(request, arena, key, scope=scope, use_pickle=True, do_locking=False)
    diskcache.lock('w')

    cache = {}
    for attrname in CACHED_USER_ATTRS:
        cache[attrname] = {}
    for userid in getUserList(request):
        u = User(request, id=userid)
        if u.valid:
            for attrname in CACHED_USER_ATTRS:
                if hasattr(u, attrname):
                    attr2id = cache[attrname]
                    value = getattr(u, attrname)
                    if isinstance(value, list):
                        for val in value:
                            attr2id[val] = userid
                    else:
                        attr2id[value] = userid

    cache_with_lowercase = addLowerCaseKeys(cache)
    setMemoryLookupCaches(request, cache_with_lowercase)
    diskcache.update(cache)
    diskcache.unlock()
    return cache


def clearLookupCaches(request):
    """kill the userid lookup cache"""
    # this triggers a rebuild of the cache.
    setMemoryLookupCaches(request, None)
    scope, arena, key = 'userdir', 'users', 'lookup'
    caching.CacheEntry(request, arena, key, scope=scope).remove()


def addLowerCaseKeys(cache):
    """add lowercased lookup keys, so we can support case-insensitive lookup"""
    c = deepcopy(cache)  # we do not want to modify cache itself
    for attrname in CACHED_USER_ATTRS:
        attr2id = c[attrname]
        attr2id_lower = c[attrname + "_lower"] = {}
        for key, value in attr2id.iteritems():
            attr2id_lower[key.lower()] = value
    return c


def getUserId(request, searchName):
    """ Get the user ID for a specific user NAME.

    @param searchName: the user name to look up
    @rtype: string
    @return: the corresponding user ID or None
    """
    return _getUserIdByKey(request, 'name', searchName)


def getUserIdByOpenId(request, openid):
    """ Get the user ID for a specific OpenID.

    @param openid: the openid to look up
    @rtype: string
    @return: the corresponding user ID or None
    """
    return _getUserIdByKey(request, 'openids', openid)


def superusers(request):
    """
    yields superuser User objects
    """
    for name in request.cfg.superuser:
        u = User(request, auth_username=name)
        if u.isSuperUser():  # this checks for addtl. criteria
            yield u


def getUserIdentification(request, username=None):
    """ Return user name or IP or '<unknown>' indicator.

    @param request: the request object
    @param username: (optional) user name
    @rtype: string
    @return: user name or IP or unknown indicator
    """
    _ = request.getText

    if username is None:
        username = request.user.name

    return username or (request.cfg.show_hosts and request.remote_addr) or _("<unknown>")


def encodePassword(cfg, pwd, salt=None, scheme=None):
    """ Encode a cleartext password using the default algorithm.

    @param cfg: the wiki config
    @param pwd: the cleartext password, (unicode)
    @param salt: the salt for the password (string) or None to generate a
                 random salt.
    @param scheme: scheme to use (by default will use cfg.password_scheme)
    @rtype: string
    @return: the password hash in apache htpasswd compatible encoding,
    """
    if scheme is None:
        scheme = cfg.password_scheme
        configured_scheme = True
    else:
        configured_scheme = False
    if scheme == '{PASSLIB}':
        return '{PASSLIB}' + cfg.cache.pwd_context.encrypt(pwd, salt=salt)
    elif scheme == '{SSHA}':
        pwd = pwd.encode('utf-8')
        if salt is None:
            salt = random_string(20)
        assert isinstance(salt, str)
        hash = hash_new('sha1', pwd)
        hash.update(salt)
        return '{SSHA}' + base64.encodestring(hash.digest() + salt).rstrip()
    else:
        # should never happen as we check the value of cfg.password_scheme
        raise NotImplementedError


class Fault(Exception):
    """something went wrong"""

class NoSuchUser(Fault):
    """raised if no such user exists"""

class UserHasNoEMail(Fault):
    """raised if user has no e-mail address in his profile"""

class MailFailed(Fault):
    """raised if e-mail sending failed"""


def set_password(request, newpass, u=None, uid=None, uname=None,
                 notify=False, skip_invalid=False, subject=None,
                 text_intro=None, text_msg=None, text_data=None):
    if uid:
        u = User(request, uid)
    elif uname:
        u = User(request, auth_username=uname)
    if u and u.exists():
        if skip_invalid and u.enc_password == '':
            return
        if not newpass:
            # set a invalid password hash
            u.enc_password = ''
        else:
            u.enc_password = encodePassword(request.cfg, newpass)
        u.save()
        if not u.email:
            raise UserHasNoEMail('User profile does not have an E-Mail address (name: %r id: %r)!' % (u.name, u.id))
        if notify and not u.disabled:
            mailok, msg = u.mailAccountData(subject=subject,
                                            text_intro=text_intro, text_msg=text_msg, text_data=text_data)
            if not mailok:
                raise MailFailed(msg)
    else:
        raise NoSuchUser('User does not exist (name: %r id: %r)!' % (u.name, u.id))


def normalizeName(name):
    """ Make normalized user name

    Prevent impersonating another user with names containing leading,
    trailing or multiple whitespace, or using invisible unicode
    characters.

    Prevent creating user page as sub page, because '/' is not allowed
    in user names.

    Prevent using ':' and ',' which are reserved by acl.

    @param name: user name, unicode
    @rtype: unicode
    @return: user name that can be used in acl lines
    """
    username_allowedchars = "'@.-_" # ' for names like O'Brian or email addresses.
                                    # "," and ":" must not be allowed (ACL delimiters).
                                    # We also allow _ in usernames for nicer URLs.
    # Strip non alpha numeric characters (except username_allowedchars), keep white space
    name = ''.join([c for c in name if c.isalnum() or c.isspace() or c in username_allowedchars])

    # Normalize white space. Each name can contain multiple
    # words separated with only one space.
    name = ' '.join(name.split())

    return name


def isValidName(request, name):
    """ Validate user name

    @param name: user name, unicode
    """
    normalized = normalizeName(name)
    return (name == normalized) and not wikiutil.isGroupPage(name, request.cfg)


def encodeList(items):
    """ Encode list of items in user data file

    Items are separated by '\t' characters.

    @param items: list unicode strings
    @rtype: unicode
    @return: list encoded as unicode
    """
    line = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        line.append(item)

    line = '\t'.join(line)
    return line

def decodeList(line):
    """ Decode list of items from user data file

    @param line: line containing list of items, encoded with encodeList
    @rtype: list of unicode strings
    @return: list of items in encoded in line
    """
    items = []
    for item in line.split('\t'):
        item = item.strip()
        if not item:
            continue
        items.append(item)
    return items

def encodeDict(items):
    """ Encode dict of items in user data file

    Items are separated by '\t' characters.
    Each item is key:value.

    @param items: dict of unicode:unicode
    @rtype: unicode
    @return: dict encoded as unicode
    """
    line = []
    for key, value in items.items():
        item = u'%s:%s' % (key, value)
        line.append(item)
    line = '\t'.join(line)
    return line

def decodeDict(line):
    """ Decode dict of key:value pairs from user data file

    @param line: line containing a dict, encoded with encodeDict
    @rtype: dict
    @return: dict  unicode:unicode items
    """
    items = {}
    for item in line.split('\t'):
        item = item.strip()
        if not item:
            continue
        key, value = item.split(':', 1)
        items[key] = value
    return items


class User:
    """ A MoinMoin User """

    def __init__(self, request, id=None, name="", password=None, auth_username="", **kw):
        """ Initialize User object

        TODO: when this gets refactored, use "uid" not builtin "id"

        @param request: the request object
        @param id: (optional) user ID
        @param name: (optional) user name
        @param password: (optional) user password (unicode)
        @param auth_username: (optional) already authenticated user name
                              (e.g. when using http basic auth) (unicode)
        @keyword auth_method: method that was used for authentication,
                              default: 'internal'
        @keyword auth_attribs: tuple of user object attribute names that are
                               determined by auth method and should not be
                               changeable by preferences, default: ().
                               First tuple element was used for authentication.
        """
        self._cfg = request.cfg
        self.valid = 0
        self.id = id
        self.auth_username = auth_username
        self.auth_method = kw.get('auth_method', 'internal')
        self.auth_attribs = kw.get('auth_attribs', ())
        self.bookmarks = {} # interwikiname: bookmark

        # create some vars automatically
        self.__dict__.update(self._cfg.user_form_defaults)

        if name:
            self.name = name
        elif auth_username: # this is needed for user autocreate
            self.name = auth_username

        # create checkbox fields (with default 0)
        for key, label in self._cfg.user_checkbox_fields:
            setattr(self, key, self._cfg.user_checkbox_defaults.get(key, 0))

        self.recoverpass_key = ""

        if password:
            self.enc_password = encodePassword(self._cfg, password)

        #self.edit_cols = 80
        self.tz_offset = int(float(self._cfg.tz_offset) * 3600)
        self.language = ""
        self.real_language = "" # In case user uses "Browser setting". For language-statistics
        self._stored = False
        self.date_fmt = ""
        self.datetime_fmt = ""
        self.quicklinks = self._cfg.quicklinks_default
        self.subscribed_pages = self._cfg.subscribed_pages_default
        self.email_subscribed_events = self._cfg.email_subscribed_events_default
        self.jabber_subscribed_events = self._cfg.jabber_subscribed_events_default
        self.theme_name = self._cfg.theme_default
        self.editor_default = self._cfg.editor_default
        self.editor_ui = self._cfg.editor_ui
        self.last_saved = str(time.time())

        # attrs not saved to profile
        self._request = request

        # we got an already authenticated username:
        check_password = None
        if not self.id and self.auth_username:
            self.id = getUserId(request, self.auth_username)
            if not password is None:
                check_password = password
        if self.id:
            self.load_from_id(check_password)
        elif self.name:
            self.id = getUserId(self._request, self.name)
            if self.id:
                # no password given should fail
                self.load_from_id(password or u'')
        # Still no ID - make new user
        if not self.id:
            self.id = self.make_id()
            if password is not None:
                self.enc_password = encodePassword(self._cfg, password)

        # "may" so we can say "if user.may.read(pagename):"
        if self._cfg.SecurityPolicy:
            self.may = self._cfg.SecurityPolicy(self)
        else:
            from MoinMoin.security import Default
            self.may = Default(self)

        if self.language and not self.language in i18n.wikiLanguages():
            self.language = 'en'

    def __repr__(self):
        return "<%s.%s at 0x%x name:%r valid:%r>" % (
            self.__class__.__module__, self.__class__.__name__,
            id(self), self.name, self.valid)

    def make_id(self):
        """ make a new unique user id """
        #!!! this should probably be a hash of REMOTE_ADDR, HTTP_USER_AGENT
        # and some other things identifying remote users, then we could also
        # use it reliably in edit locking
        from random import randint
        return "%s.%d" % (str(time.time()), randint(0, 65535))

    def create_or_update(self, changed=False):
        """ Create or update a user profile

        @param changed: bool, set this to True if you updated the user profile values
        """
        if not self.valid and not self.disabled or changed: # do we need to save/update?
            self.save() # yes, create/update user profile

    def __filename(self):
        """ Get filename of the user's file on disk

        @rtype: string
        @return: full path and filename of user account file
        """
        return os.path.join(self._cfg.user_dir, self.id or "...NONE...")

    def exists(self):
        """ Do we have a user account for this user?

        @rtype: bool
        @return: true, if we have a user account
        """
        return os.path.exists(self.__filename())

    def remove(self):
        """ Remove user profile from disk """
        os.remove(self.__filename())

    def load_from_id(self, password=None):
        """ Load user account data from disk.

        Can only load user data if the id number is already known.

        This loads all member variables, except "id" and "valid" and
        those starting with an underscore.

        @param password: If not None, then the given password must match the
                         password in the user account file.
        """
        if not self.exists():
            return

        data = codecs.open(self.__filename(), "r", config.charset).readlines()
        user_data = {'enc_password': ''}
        for line in data:
            if line[0] == '#':
                continue

            try:
                key, val = line.strip().split('=', 1)
                if key not in self._cfg.user_transient_fields and key[0] != '_':
                    # Decode list values
                    if key.endswith('[]'):
                        key = key[:-2]
                        val = decodeList(val)
                    # Decode dict values
                    elif key.endswith('{}'):
                        key = key[:-2]
                        val = decodeDict(val)
                    # for compatibility reading old files, keep these explicit
                    # we will store them with [] appended
                    elif key in ['quicklinks', 'subscribed_pages', 'subscribed_events']:
                        val = decodeList(val)
                    user_data[key] = val
            except ValueError:
                pass

        # Validate data from user file. In case we need to change some
        # values, we set 'changed' flag, and later save the user data.
        changed = 0

        if password is not None:
            # Check for a valid password, possibly changing storage
            valid, changed = self._validatePassword(user_data, password)
            if not valid:
                return

        # Remove ignored checkbox values from user data
        for key, label in self._cfg.user_checkbox_fields:
            if key in user_data and key in self._cfg.user_checkbox_disable:
                del user_data[key]

        # Copy user data into user object
        for key, val in user_data.items():
            vars(self)[key] = val

        self.tz_offset = int(self.tz_offset)

        # Remove old unsupported attributes from user data file.
        remove_attributes = ['passwd', 'show_emoticons']
        for attr in remove_attributes:
            if hasattr(self, attr):
                delattr(self, attr)
                changed = 1

        # make sure checkboxes are boolean
        for key, label in self._cfg.user_checkbox_fields:
            try:
                setattr(self, key, int(getattr(self, key)))
            except ValueError:
                setattr(self, key, 0)

        # convert (old) hourly format to seconds
        if -24 <= self.tz_offset and self.tz_offset <= 24:
            self.tz_offset = self.tz_offset * 3600

        if not self.disabled:
            self.valid = 1

        # Mark this user as stored so saves don't send
        # the "user created" event
        self._stored = True

        # If user data has been changed, save fixed user data.
        if changed:
            self.save()

    def _validatePassword(self, data, password):
        """
        Check user password.

        This is a private method and should not be used by clients.

        @param data: dict with user data (from storage)
        @param password: password to verify [unicode]
        @rtype: 2 tuple (bool, bool)
        @return: password is valid, enc_password changed
        """
        epwd = data['enc_password']

        # If we have no password set, we don't accept login with username
        if not epwd:
            return False, False

        # require non empty password
        if not password:
            return False, False

        password_correct = recompute_hash = False
        wanted_scheme = self._cfg.password_scheme

        # Check password and upgrade weak hashes to strong default algorithm:
        for scheme in config.password_schemes_supported:
            if epwd.startswith(scheme):
                is_passlib = False
                d = epwd[len(scheme):]

                if scheme == '{PASSLIB}':
                    # a password hash to be checked by passlib library code
                    if not self._cfg.passlib_support:
                        logging.error('in user profile %r, password hash with {PASSLIB} scheme encountered, but passlib_support is False' % (self.id, ))
                    else:
                        pwd_context = self._cfg.cache.pwd_context
                        try:
                            password_correct = pwd_context.verify(password, d)
                        except ValueError, err:
                            # can happen for unknown scheme
                            logging.error('in user profile %r, verifying the passlib pw hash crashed [%s]' % (self.id, str(err)))
                        if password_correct:
                            # check if we need to recompute the hash. this is needed if either the
                            # passlib hash scheme / hash params changed or if we shall change to a
                            # builtin hash scheme (not recommended):
                            recompute_hash = pwd_context.hash_needs_update(d) or wanted_scheme != '{PASSLIB}'

                else:
                    # a password hash to be checked by legacy, builtin code
                    if scheme == '{SSHA}':
                        d = base64.decodestring(d)
                        salt = d[20:]
                        hash = hash_new('sha1', password.encode('utf-8'))
                        hash.update(salt)
                        enc = base64.encodestring(hash.digest() + salt).rstrip()

                    elif scheme == '{SHA}':
                        enc = base64.encodestring(
                            hash_new('sha1', password.encode('utf-8')).digest()).rstrip()

                    elif scheme == '{APR1}':
                        # d is of the form "$apr1$<salt>$<hash>"
                        salt = d.split('$')[2]
                        enc = md5crypt.apache_md5_crypt(password.encode('utf-8'),
                                                        salt.encode('ascii'))
                    elif scheme == '{MD5}':
                        # d is of the form "$1$<salt>$<hash>"
                        salt = d.split('$')[2]
                        enc = md5crypt.unix_md5_crypt(password.encode('utf-8'),
                                                      salt.encode('ascii'))
                    elif scheme == '{DES}':
                        if crypt is None:
                            return False, False
                        # d is 2 characters salt + 11 characters hash
                        salt = d[:2]
                        enc = crypt.crypt(password.encode('utf-8'), salt.encode('ascii'))

                    else:
                        logging.error('in user profile %r, password hash with unknown scheme encountered: %r' % (self.id, scheme))
                        raise NotImplementedError

                    if safe_str_equal(epwd, scheme + enc):
                        password_correct = True
                        recompute_hash = scheme != wanted_scheme

                if recompute_hash:
                    data['enc_password'] = encodePassword(self._cfg, password)
                return password_correct, recompute_hash

        # unsupported algorithm
        return False, False

    def persistent_items(self):
        """ items we want to store into the user profile """
        return [(key, value) for key, value in vars(self).items()
                    if key not in self._cfg.user_transient_fields and key[0] != '_']

    def save(self):
        """ Save user account data to user account file on disk.

        This saves all member variables, except "id" and "valid" and
        those starting with an underscore.
        """
        if not self.id:
            return

        user_dir = self._cfg.user_dir
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        self.last_saved = str(time.time())

        # !!! should write to a temp file here to avoid race conditions,
        # or even better, use locking

        data = codecs.open(self.__filename(), "w", config.charset)
        data.write("# Data saved '%s' for id '%s'\n" % (
            time.strftime(self._cfg.datetime_fmt, time.localtime(time.time())),
            self.id))
        attrs = self.persistent_items()
        attrs.sort()
        for key, value in attrs:
            # Encode list values
            if isinstance(value, list):
                key += '[]'
                value = encodeList(value)
            # Encode dict values
            elif isinstance(value, dict):
                key += '{}'
                value = encodeDict(value)
            line = u"%s=%s" % (key, unicode(value))
            line = line.replace('\n', ' ').replace('\r', ' ') # no lineseps
            data.write(line + '\n')
        data.close()

        if not self.disabled:
            self.valid = 1

        self.updateLookupCaches()

        if not self._stored:
            self._stored = True
            event = events.UserCreatedEvent(self._request, self)
            events.send_event(event)

        # update page subscriber's cache after saving user preferences
        self.updatePageSubCache()

    # -----------------------------------------------------------------
    # Time and date formatting

    def getTime(self, tm):
        """ Get time in user's timezone.

        @param tm: time (UTC UNIX timestamp)
        @rtype: int
        @return: tm tuple adjusted for user's timezone
        """
        return timefuncs.tmtuple(tm + self.tz_offset)


    def getFormattedDate(self, tm):
        """ Get formatted date adjusted for user's timezone.

        @param tm: time (UTC UNIX timestamp)
        @rtype: string
        @return: formatted date, see cfg.date_fmt
        """
        date_fmt = self.date_fmt or self._cfg.date_fmt
        return time.strftime(date_fmt, self.getTime(tm))


    def getFormattedDateTime(self, tm):
        """ Get formatted date and time adjusted for user's timezone.

        @param tm: time (UTC UNIX timestamp)
        @rtype: string
        @return: formatted date and time, see cfg.datetime_fmt
        """
        datetime_fmt = self.datetime_fmt or self._cfg.datetime_fmt
        return time.strftime(datetime_fmt, self.getTime(tm))

    # -----------------------------------------------------------------
    # Bookmark

    def setBookmark(self, tm):
        """ Set bookmark timestamp.

        @param tm: timestamp
        """
        if self.valid:
            interwikiname = self._cfg.interwikiname or u''
            bookmark = unicode(tm)
            self.bookmarks[interwikiname] = bookmark
            self.save()

    def getBookmark(self):
        """ Get bookmark timestamp.

        @rtype: int
        @return: bookmark timestamp or None
        """
        bm = None
        interwikiname = self._cfg.interwikiname or u''
        if self.valid:
            try:
                bm = int(self.bookmarks[interwikiname])
            except (ValueError, KeyError):
                pass
        return bm

    def delBookmark(self):
        """ Removes bookmark timestamp.

        @rtype: int
        @return: 0 on success, 1 on failure
        """
        interwikiname = self._cfg.interwikiname or u''
        if self.valid:
            try:
                del self.bookmarks[interwikiname]
            except KeyError:
                return 1
            self.save()
            return 0
        return 1

    # -----------------------------------------------------------------
    # Subscribe

    def getSubscriptionList(self):
        """ Get list of pages this user has subscribed to

        @rtype: list
        @return: pages this user has subscribed to
        """
        return self.subscribed_pages

    def isSubscribedTo(self, pagelist):
        """ Check if user subscription matches any page in pagelist.

        The subscription list may contain page names or interwiki page
        names. e.g 'Page Name' or 'WikiName:Page_Name'

        @param pagelist: list of pages to check for subscription
        @rtype: bool
        @return: if user is subscribed any page in pagelist
        """
        if not self.valid:
            return False

        import re
        # Create a new list with both names and interwiki names.
        pages = pagelist[:]
        if self._cfg.interwikiname:
            pages += [self._interWikiName(pagename) for pagename in pagelist]
        # Create text for regular expression search
        text = '\n'.join(pages)

        for pattern in self.getSubscriptionList():
            # Try simple match first
            if pattern in pages:
                return True
            # Try regular expression search, skipping bad patterns
            try:
                pattern = re.compile(r'^%s$' % pattern, re.M)
            except re.error:
                continue
            if pattern.search(text):
                return True

        return False

    def subscribe(self, pagename):
        """ Subscribe to a wiki page.

        To enable shared farm users, if the wiki has an interwiki name,
        page names are saved as interwiki names.

        @param pagename: name of the page to subscribe
        @type pagename: unicode
        @rtype: bool
        @return: if page was subscribed
        """
        if self._cfg.interwikiname:
            pagename = self._interWikiName(pagename)

        if pagename not in self.subscribed_pages:
            self.subscribed_pages.append(pagename)
            self.save()

            # Send a notification
            from MoinMoin.events import SubscribedToPageEvent, send_event
            e = SubscribedToPageEvent(self._request, pagename, self.name)
            send_event(e)
            return True

        return False

    def unsubscribe(self, pagename):
        """ Unsubscribe a wiki page.

        Try to unsubscribe by removing non-interwiki name (leftover
        from old use files) and interwiki name from the subscription
        list.

        Its possible that the user will be subscribed to a page by more
        then one pattern. It can be both pagename and interwiki name,
        or few patterns that all of them match the page. Therefore, we
        must check if the user is still subscribed to the page after we
        try to remove names from the list.

        @param pagename: name of the page to subscribe
        @type pagename: unicode
        @rtype: bool
        @return: if unsubscrieb was successful. If the user has a
            regular expression that match, it will always fail.
        """
        changed = False
        if pagename in self.subscribed_pages:
            self.subscribed_pages.remove(pagename)
            changed = True

        interWikiName = self._interWikiName(pagename)
        if interWikiName and interWikiName in self.subscribed_pages:
            self.subscribed_pages.remove(interWikiName)
            changed = True

        if changed:
            self.save()
        return not self.isSubscribedTo([pagename])

    def updatePageSubCache(self):
        """ When a user profile is saved, we update the page subscriber's cache """

        scope, arena, key = 'userdir', 'users', 'pagesubscriptions'

        cache = caching.CacheEntry(self._request, arena=arena, key=key, scope=scope, use_pickle=True, do_locking=False)
        if not cache.exists():
            return  # if no cache file exists, just don't do anything

        cache.lock('w')
        page_sub = cache.content()

        # we only store entries for valid users with some page subscriptions
        if self.valid and self.subscribed_pages:
            page_sub[self.id] = {
                'name': self.name,
                'email': self.email,
                'subscribed_pages': self.subscribed_pages,
            }
        elif page_sub.get(self.id):
            del page_sub[self.id]

        cache.update(page_sub)
        cache.unlock()

    def updateLookupCaches(self):
        """ When a user profile is saved, we update the userid lookup caches """

        scope, arena, key = 'userdir', 'users', 'lookup'

        diskcache = caching.CacheEntry(self._request, arena=arena, key=key, scope=scope, use_pickle=True, do_locking=False)
        if not diskcache.exists():
            return  # if no cache file exists, just don't do anything

        diskcache.lock('w')
        cache = diskcache.content()
        userid = self.id

        # first remove all old entries mapping to this userid:
        for attrname in CACHED_USER_ATTRS:
            attr2id = cache[attrname]
            for key, value in attr2id.items():
                if value == userid:
                    del attr2id[key]

        # then, if user is valid, update with the current attr values:
        if self.valid:
            for attrname in CACHED_USER_ATTRS:
                if hasattr(self, attrname):
                    value = getattr(self, attrname)
                    if value:
                        # we do not store empty values, likely not unique
                        attr2id = cache[attrname]
                        if isinstance(value, list):
                            for val in value:
                                attr2id[val] = userid
                        else:
                            attr2id[value] = userid

        cache_with_lowercase = addLowerCaseKeys(cache)
        setMemoryLookupCaches(self._request, cache_with_lowercase)
        diskcache.update(cache)
        diskcache.unlock()

    # -----------------------------------------------------------------
    # Quicklinks

    def getQuickLinks(self):
        """ Get list of pages this user wants in the navibar

        @rtype: list
        @return: quicklinks from user account
        """
        return self.quicklinks

    def isQuickLinkedTo(self, pagelist):
        """ Check if user quicklink matches any page in pagelist.

        @param pagelist: list of pages to check for quicklinks
        @rtype: bool
        @return: if user has quicklinked any page in pagelist
        """
        if not self.valid:
            return False

        for pagename in pagelist:
            if pagename in self.quicklinks:
                return True
            interWikiName = self._interWikiName(pagename)
            if interWikiName and interWikiName in self.quicklinks:
                return True

        return False

    def addQuicklink(self, pagename):
        """ Adds a page to the user quicklinks

        If the wiki has an interwiki name, all links are saved as
        interwiki names. If not, as simple page name.

        @param pagename: page name
        @type pagename: unicode
        @rtype: bool
        @return: if pagename was added
        """
        changed = False
        interWikiName = self._interWikiName(pagename)
        if interWikiName:
            if pagename in self.quicklinks:
                self.quicklinks.remove(pagename)
                changed = True
            if interWikiName not in self.quicklinks:
                self.quicklinks.append(interWikiName)
                changed = True
        else:
            if pagename not in self.quicklinks:
                self.quicklinks.append(pagename)
                changed = True

        if changed:
            self.save()
        return changed

    def removeQuicklink(self, pagename):
        """ Remove a page from user quicklinks

        Remove both interwiki and simple name from quicklinks.

        @param pagename: page name
        @type pagename: unicode
        @rtype: bool
        @return: if pagename was removed
        """
        changed = False
        interWikiName = self._interWikiName(pagename)
        if interWikiName and interWikiName in self.quicklinks:
            self.quicklinks.remove(interWikiName)
            changed = True
        if pagename in self.quicklinks:
            self.quicklinks.remove(pagename)
            changed = True

        if changed:
            self.save()
        return changed

    def _interWikiName(self, pagename):
        """ Return the inter wiki name of a page name

        @param pagename: page name
        @type pagename: unicode
        """
        if not self._cfg.interwikiname:
            return None

        return "%s:%s" % (self._cfg.interwikiname, pagename)

    # -----------------------------------------------------------------
    # Trail

    def _wantTrail(self):
        return (not self.valid and self._request.cfg.cookie_lifetime[0]  # anon sessions enabled
                or self.valid and (self.show_page_trail or self.remember_last_visit))  # logged-in session

    def addTrail(self, page):
        """ Add page to trail.

        @param page: the page (object) to add to the trail
        """
        if self._wantTrail():
            pagename = page.page_name
            # Add only existing pages that the user may read
            if not (page.exists() and self._request.user.may.read(pagename)):
                return

            # Save interwiki links internally
            if self._cfg.interwikiname:
                pagename = self._interWikiName(pagename)

            trail = self._request.session.get('trail', [])
            trail_current = trail[:]

            # Don't append tail to trail ;)
            if trail and trail[-1] == pagename:
                return

            # Append new page, limiting the length
            trail = [p for p in trail if p != pagename]
            pagename_stripped = pagename.strip()
            if pagename_stripped:
                trail.append(pagename_stripped)
            trail = trail[-self._cfg.trail_size:]
            if trail != trail_current:
                # we only modify the session if we have something different:
                self._request.session['trail'] = trail

    def getTrail(self):
        """ Return list of recently visited pages.

        @rtype: list
        @return: pages in trail
        """
        if self._wantTrail():
            trail = self._request.session.get('trail', [])
        else:
            trail = []
        return trail

    # -----------------------------------------------------------------
    # Other

    def isCurrentUser(self):
        """ Check if this user object is the user doing the current request """
        return self._request.user.name == self.name

    def isSuperUser(self):
        """ Check if this user is superuser """
        if not self.valid:
            return False
        request = self._request
        if request.cfg.DesktopEdition and request.remote_addr == '127.0.0.1':
            # the DesktopEdition gives any local user superuser powers
            return True
        superusers = request.cfg.superuser
        assert isinstance(superusers, (list, tuple))
        return self.name and self.name in superusers

    def host(self):
        """ Return user host """
        _ = self._request.getText
        host = self.isCurrentUser() and self._cfg.show_hosts and self._request.remote_addr
        return host or _("<unknown>")

    def wikiHomeLink(self):
        """ Return wiki markup usable as a link to the user homepage,
            it doesn't matter whether it already exists or not.
        """
        wikiname, pagename = wikiutil.getInterwikiHomePage(self._request, self.name)
        if wikiname == 'Self':
            if wikiutil.isStrictWikiname(self.name):
                markup = pagename
            else:
                markup = '[[%s]]' % pagename
        else:
            markup = '[[%s:%s]]' % (wikiname, pagename)
        return markup

    def signature(self):
        """ Return user signature using wiki markup

        Users sign with a link to their homepage.
        Visitors return their host address.

        TODO: The signature use wiki format only, for example, it will
        not create a link when using rst format. It will also break if
        we change wiki syntax.
        """
        if self.name:
            return self.wikiHomeLink()
        else:
            return self.host()

    def generate_recovery_token(self):
        key = random_string(64, "abcdefghijklmnopqrstuvwxyz0123456789")
        msg = str(int(time.time()))
        h = hmac_new(key, msg).hexdigest()
        self.recoverpass_key = key
        self.save()
        return msg + '-' + h

    def apply_recovery_token(self, tok, newpass):
        parts = tok.split('-')
        if len(parts) != 2:
            return False
        try:
            stamp = int(parts[0])
        except ValueError:
            return False
        lifetime = self._request.cfg.recovery_token_lifetime * 3600
        if time.time() > stamp + lifetime:
            return False
        # check hmac
        # key must be of type string
        h = hmac_new(str(self.recoverpass_key), str(stamp)).hexdigest()
        if not safe_str_equal(h, parts[1]):
            return False
        self.recoverpass_key = ""
        self.enc_password = encodePassword(self._cfg, newpass)
        self.save()
        return True

    def mailAccountData(self, cleartext_passwd=None,
                        subject=None,
                        text_intro=None, text_msg=None, text_data=None):
        """ Mail a user who forgot his password a message enabling
            him to login again.
        """
        from MoinMoin.mail import sendmail
        _ = self._request.getText

        if not self.email:
            return False, "user has no E-Mail address in his profile."

        tok = self.generate_recovery_token()

        if subject is None:
            subject = _('[%(sitename)s] Your wiki account data')
        subject = subject % dict(sitename=self._cfg.sitename or "Wiki")
        if text_intro is None:
            text_intro = ''
        if text_msg is None:
            text_msg = _("""\
Somebody has requested to email you a password recovery token.

If you lost your password, please go to the password reset URL below or
go to the password recovery page again and enter your username and the
recovery token.
""")
        if text_data is None:
            text_data = _("""\
Login Name: %s

Password recovery token: %s

Password reset URL: %s?action=recoverpass&name=%s&token=%s
""")
        # note: text_intro is for custom stuff, we do not have i18n for it anyway
        text = text_intro + '\n' + _(text_msg) + '\n' + _(text_data) % (
                        self.name,
                        tok,
                        self._request.url, # use full url, including current page
                        url_quote_plus(self.name),
                        tok, )

        mailok, msg = sendmail.sendmail(self._request, [self.email], subject,
                                    text, mail_from=self._cfg.mail_from)
        return mailok, msg

