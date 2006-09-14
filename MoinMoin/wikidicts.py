# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Dictionary / Group Functions

    @copyright: 2003-2006 by Thomas Waldmann, MoinMoin:ThomasWaldmann
    @copyright: 2003 by Gustavo Niemeyer, http://moin.conectiva.com.br/GustavoNiemeyer
    @license: GNU GPL, see COPYING for details.
"""
import re, time, os

#import copy #broken, see comments at top of this file:
from MoinMoin.support import copy

# cPickle can encode normal and Unicode strings
# see http://docs.python.org/lib/node66.html
try:
    import cPickle as pickle
except ImportError:
    import pickle

# Set pickle protocol, see http://docs.python.org/lib/node64.html
PICKLE_PROTOCOL = pickle.HIGHEST_PROTOCOL

from MoinMoin import config, caching, wikiutil, Page, logfile
from MoinMoin.logfile.editlog import EditLog

# Version of the internal data structure which is pickled
# Please increment if you have changed the structure
DICTS_PICKLE_VERSION = 5


class DictBase:
    """ Base class for wiki dicts

    To use this class, sub class it and override regex and initFromText.
    """
    # Regular expression used to parse text - sub class should override this
    regex = ''

    def __init__(self, request, name):
        """ Initialize, starting from <nothing>.

        Create a dict from a wiki page.
        """
        self.name = name

        self.initRegex()

        # Get text from page named 'name'
        p = Page.Page(request, name)
        text = p.get_raw_body()
        self.initFromText(text)

    def initRegex(cls):
        """ Make it a class attribute to avoid it being pickled. """
        cls.regex = re.compile(cls.regex, re.MULTILINE | re.UNICODE)
    initRegex = classmethod(initRegex)

    def initFromText(self, text):
        raise NotImplementedError('sub classes should override this')

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()
    
    def get_dict(self):
        return self._dict

    def has_key(self, key):
        return self._dict.has_key(key)

    def get(self, key, default):
        return self._dict.get(key, default)

    def __getitem__(self, key):
        return self._dict[key]

    def __repr__(self):
        return "<DictBase name=%r items=%r>" % (self.name, self._dict.items())

class Dict(DictBase):
    """ Mapping of keys to values in a wiki page

       How a Dict definition page should look like:

       any text ignored
        key1:: value1
        * ignored, too
        key2:: value2 containing spaces
        ...
        keyn:: ....
       any text ignored      
    """
    # Key:: Value - ignore all but key:: value pairs, strip whitespace
    regex = r'^ (?P<key>.+?):: (?P<val>.*?) *$'

    def initFromText(self, text):
        """ Create dict from keys and values in text

        Invoked by __init__, also useful for testing without a page.
        """
        self._dict = {}
        for match in self.regex.finditer(text):
            key, val = match.groups()
            self._dict[key] = val

    def __repr__(self):
        return "<Dict name=%r items=%r>" % (self.name, self._dict.items())

class Group(DictBase):
    """ Group of users, of pages, of whatever

    How a Group definition page should look like:

    any text ignored
     * member1
      * ignored, too
     * member2
     * ....
     * memberN
    any text ignored

    if there are any free links using ["free link"] notation, the markup
    is stripped from the member 
    """
    # * Member - ignore all but first level list items, strip whitespace
    # Strip free links markup if exists
    regex = r'^ \* +(?:\[\")?(?P<member>.+?)(?:\"\])? *$'

    def initFromText(self, text):
        """ Create dict from group members in text

        Invoked by __init__, also useful for testing without a page.
        """
        self._dict = {}
        for match in self.regex.finditer(text):
            self._dict[match.group('member')] = 1

    def members(self):
        return self._dict.keys()

    def addmembers(self, members):
        for m in members:
            self.addmember(m)

    def addmember(self, member):
        self._dict[member] = 1

    def has_member(self, member):
        return self._dict.has_key(member)

    def _expandgroup(self, groupdict, name):
        """ Recursively expand group

        If a group contain another group, the members of that group are
        added into the the group. The group name itself is not replaced.

        Given two groups:

            MainGruop = [A, SubGroup]
            SubGroup = [B, C]

        MainGroup is expanded to:

            MainGroup = [A, SubGroup, B, C]
            
        This behavior is important for things like SystemPagesGroup,
        when we like to know if a page is a system page group. page may
        be a page or a page group, like SystemPagesGroupInFrenchGroup.

        This behavior has no meaning for users groups used in ACL,
        because user can not use a group name. Note that if you allow a
        user to use a group name, one can gain a sub group privileges by
        registering a user with that group name.
        """
        groupmembers = groupdict.members(name)
        members = {}
        for member in groupmembers:
            # Skip self duplicates
            if member == self.name:
                continue
            # Add member and its children
            members[member] = 1
            if groupdict.hasgroup(member):
                members.update(self._expandgroup(groupdict, member))
        return members

    def expandgroups(self, groupdict):
        """ Invoke _expandgroup to recursively expand groups """
        self._dict = self._expandgroup(groupdict, self.name)

    def __repr__(self):
        return "<Group name=%r items=%r>" % (self.name, self._dict.keys())


class DictDict:
    """a dictionary of Dict objects

       Config:
           cfg.page_dict_regex
               Default: ".*Dict$"  Defs$ Vars$ ???????????????????
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.dictdict = {}
        self.namespace_timestamp = 0
        self.pageupdate_timestamp = 0
        self.base_timestamp = 0
        self.picklever = DICTS_PICKLE_VERSION

    def has_key(self, dictname, key):
        dict = self.dictdict.get(dictname)
        return dict and dict.has_key(key)

    def keys(self, dictname):
        """get keys of dict <dictname>"""
        try:
            dict = self.dictdict[dictname]
        except KeyError:
            return []
        return dict.keys()

    def values(self, dictname):
        """get values of dict <dictname>"""
        try:
            dict = self.dictdict[dictname]
        except KeyError:
            return []
        return dict.values()

    def dict(self, dictname):
        """get dict <dictname>"""
        try:
            dict = self.dictdict[dictname]
        except KeyError:
            return {}
        return dict

    def adddict(self, request, dictname):
        """add a new dict (will be read from the wiki page)"""
        self.dictdict[dictname] = Dict(request, dictname)

    def has_dict(self, dictname):
        return self.dictdict.has_key(dictname)

    def keydict(self, key):
        """list all dicts that contain key"""
        dictlist = []
        for dict in self.dictdict.values():
            if dict.has_key(key):
                dictlist.append(dict.name)
        return dictlist


class GroupDict(DictDict):
    """a dictionary of Group objects

       Config:
           cfg.page_group_regex
               Default: ".*Group$"
    """

    def __init__(self, request):
        self.cfg = request.cfg
        self.request = request

    def reset(self):
        self.dictdict = {}
        self.groupdict = {} # unexpanded groups
        self.namespace_timestamp = 0
        self.pageupdate_timestamp = 0
        self.base_timestamp = 0
        self.picklever = DICTS_PICKLE_VERSION

    def has_member(self, groupname, member):
        group = self.dictdict.get(groupname)
        return group and group.has_member(member)

    def members(self, groupname):
        """get members of group <groupname>"""
        try:
            group = self.dictdict[groupname]
        except KeyError:
            return []
        return group.members()

    def addgroup(self, request, groupname):
        """add a new group (will be read from the wiki page)"""
        grp = Group(request, groupname)
        self.dictdict[groupname] = grp
        self.groupdict[groupname] = grp

    def hasgroup(self, groupname):
        return self.groupdict.has_key(groupname)

    def membergroups(self, member):
        """list all groups where member is a member of"""
        grouplist = []
        for group in self.dictdict.values():
            if group.has_member(member):
                grouplist.append(group.name)
        return grouplist

    def scandicts(self):
        """scan all pages matching the dict / group regex and init the dictdict"""
        dump = 0
        request = self.request

        # Save now in our internal version format
        now = wikiutil.timestamp2version(int(time.time()))
        try:
            lastchange = EditLog(request).date()
        except logfile.LogMissing:
            lastchange = 0
            dump = 1

        arena = 'wikidicts'
        key = 'dicts_groups'
        try:
            self.__dict__.update(self.cfg.cache.DICTS_DATA)
        except AttributeError:
            try:
                cache = caching.CacheEntry(request, arena, key, scope='wiki')
                data = pickle.loads(cache.content())
                self.__dict__.update(data)

                # invalidate the cache if the pickle version changed
                if self.picklever != DICTS_PICKLE_VERSION:
                    self.reset()
                    dump = 1
            except:
                self.reset()
                dump = 1

        if lastchange >= self.namespace_timestamp or dump:
            isdict = self.cfg.cache.page_dict_regex.search
            isgroup = self.cfg.cache.page_group_regex.search

            # check for new groups / dicts from time to time...
            if now - self.namespace_timestamp >= wikiutil.timestamp2version(60): # 60s
                # Get all pages in the wiki - without user filtering using filter
                #function - this make the page list about 10 times faster.
                dictpages = request.rootpage.getPageList(user='', filter=isdict)
                grouppages = request.rootpage.getPageList(user='', filter=isgroup)

                # remove old entries when dict or group page have been deleted,
                # add entries when pages have been added
                # use copies because the dicts are shared via cfg.cache.DICTS_DATA
                #  and must not be modified
                olddictdict = self.dictdict.copy()
                oldgroupdict = self.groupdict.copy()
                self.dictdict = {}
                self.groupdict = {}

                for pagename in dictpages:
                    if olddictdict.has_key(pagename):
                        # keep old
                        self.dictdict[pagename] = olddictdict[pagename]
                        del olddictdict[pagename]
                    else:
                        self.adddict(request, pagename)
                        dump = 1

                for pagename in grouppages:
                    if olddictdict.has_key(pagename):
                        # keep old
                        self.dictdict[pagename] = olddictdict[pagename]
                        self.groupdict[pagename] = oldgroupdict[pagename]
                        del olddictdict[pagename]
                    else:
                        self.addgroup(request, pagename)
                        dump = 1

                if olddictdict: # dict page was deleted
                    dump = 1

                self.namespace_timestamp = now

            # check if groups / dicts have been modified on disk
            for pagename in self.dictdict.keys():
                if Page.Page(request, pagename).mtime_usecs() >= self.pageupdate_timestamp:
                    if isdict(pagename):
                        self.adddict(request, pagename)
                    elif isgroup(pagename):
                        self.addgroup(request, pagename)
                    dump = 1
            self.pageupdate_timestamp = now

            if not self.base_timestamp:
                self.base_timestamp = int(time.time())

        data = {
            "namespace_timestamp": self.namespace_timestamp,
            "pageupdate_timestamp": self.pageupdate_timestamp,
            "base_timestamp": self.base_timestamp,
            "dictdict": self.dictdict,
            "groupdict": self.groupdict,
            "picklever": self.picklever
        }

        if dump:
            # copy unexpanded groups to self.dictdict
            for name, grp in self.groupdict.items():
                self.dictdict[name] = copy.deepcopy(grp)
            # expand groups
            for name in self.groupdict:
                self.dictdict[name].expandgroups(self)

            cache = caching.CacheEntry(request, arena, key, scope='wiki')
            cache.update(pickle.dumps(data, PICKLE_PROTOCOL))

        # remember it (persistent environments)
        self.cfg.cache.DICTS_DATA = data

