# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Dictionary / Group Functions

    @copyright: 2003-2007 MoinMoin:ThomasWaldmann,
                2003 by Gustavo Niemeyer
    @license: GNU GPL, see COPYING for details.
"""
import re, time

from MoinMoin.support import copy

from MoinMoin import caching, wikiutil, Page, logfile
from MoinMoin.logfile.editlog import EditLog

# Version of the internal data structure which is pickled.
# Please increment if you have changed the structure.
DICTS_PICKLE_VERSION = 6


class DictBase(dict):
    """ Base class for wiki dicts

    To use this class, subclass it and override regex and initFromText.
    """
    def __init__(self, request=None, pagename=None):
        dict.__init__(self)
        self.name = None
        if request is not None and pagename is not None:
            self.loadFromPage(request, pagename)

    # Regular expression used to parse text - subclass should override this
    regex = ''
    def initRegex(cls):
        """ Make it a class attribute to avoid it being pickled. """
        cls.regex = re.compile(cls.regex, re.MULTILINE | re.UNICODE)
    initRegex = classmethod(initRegex)

    def loadFromPage(self, request, name):
        """ load the dict from wiki page <name>'s content """
        self.name = name
        self.initRegex()
        text = Page.Page(request, name).get_raw_body()
        self.initFromText(text)

    def initFromText(self, text):
        """ parse the wiki page text and init the dict from it """
        raise NotImplementedError('subclasses should override this')


class Dict(DictBase):
    """ Mapping of keys to values in a wiki page.

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
        for match in self.regex.finditer(text):
            key, val = match.groups()
            self[key] = val

    def __repr__(self):
        return "<Dict name=%r items=%r>" % (self.name, self.items())


class Group(DictBase):
    """ Group of users, of pages, of whatever.

    How a Group definition page should look like:

    any text ignored
     * member1
      * ignored, too
     * member2
     * ....
     * memberN
    any text ignored

    If there are any free links using ["free link"] notation, the markup
    is stripped from the member.
    """
    # * Member - ignore all but first level list items, strip whitespace,
    # strip free links markup if exists.
    regex = r'^ \* +(?:\[\")?(?P<member>.+?)(?:\"\])? *$'

    def initFromText(self, text):
        for match in self.regex.finditer(text):
            member = match.group('member')
            self.addmember(member)

    def members(self):
        """ return the group's members """
        return self.keys()

    def addmembers(self, members):
        """ add a list of members to the group """
        for m in members:
            self.addmember(m)

    def addmember(self, member):
        """ add a member to the group """
        self[member] = 1

    def has_member(self, member):
        """ check if the group has member <member> """
        return self.has_key(member)

    def __repr__(self):
        return "<Group name=%r items=%r>" % (self.name, self.keys())


class DictDict:
    """ a dictionary of Dict objects

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
        """ check if we have key <key> in dict <dictname> """
        d = self.dictdict.get(dictname)
        return d and d.has_key(key)

    def keys(self, dictname):
        """ get keys of dict <dictname> """
        try:
            d = self.dictdict[dictname]
        except KeyError:
            return []
        return d.keys()

    def values(self, dictname):
        """ get values of dict <dictname> """
        try:
            d = self.dictdict[dictname]
        except KeyError:
            return []
        return d.values()

    def dict(self, dictname):
        """ get dict <dictname> """
        try:
            d = self.dictdict[dictname]
        except KeyError:
            return {}
        return d

    def adddict(self, request, dictname):
        """ add a new dict (will be read from the wiki page) """
        self.dictdict[dictname] = Dict(request, dictname)

    def has_dict(self, dictname):
        """ check if we have a dict <dictname> """
        return self.dictdict.has_key(dictname)

    def keydict(self, key):
        """ list all dicts that contain key """
        dictlist = []
        for d in self.dictdict.values():
            if d.has_key(key):
                dictlist.append(d.name)
        return dictlist


class GroupDict(DictDict):
    """ a dictionary of Group objects

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
        """ check if we have <member> as a member of group <groupname> """
        group = self.dictdict.get(groupname)
        return group and group.has_member(member)

    def members(self, groupname):
        """ get members of group <groupname> """
        try:
            group = self.dictdict[groupname]
        except KeyError:
            return []
        return group.members()

    def addgroup(self, request, groupname):
        """ add a new group (will be read from the wiki page) """
        grp = Group(request, groupname)
        self.groupdict[groupname] = grp
        self.expand_groups()

    def hasgroup(self, groupname):
        """ check if we have a dict <dictname> """
        return self.groupdict.has_key(groupname)

    def __getitem__(self, name):
        return self.groupdict[name]

    def membergroups(self, member):
        """ list all groups where member is a member of """
        grouplist = []
        for group in self.dictdict.values():
            if group.has_member(member):
                grouplist.append(group.name)
        return grouplist

    def expand_groups(self):
        """ copy expanded groups to self.dictdict """
        for name in self.groupdict:
            members, groups = self.expand_group(name)
            members.update(groups)
            grp = Group()
            grp.update(members)
            self.dictdict[name] = grp

    def expand_group(self, name):
        """ Recursively expand group <name>, using the groupdict (which is a not expanded
            dict of all group names -> group dicts). We return a flat list of group member
            names and group names.

        Given a groupdict (self) with two groups:

            MainGroup: [A, SubGroup]
            SubGroup: [B, C]

        MainGroup is expanded to:

            self.expand_group('MainGroup') -> [A, B, C], [MainGroup, SubGroup]
        """
        groups = {name: 1}
        members = {}
        groupmembers = self[name].keys()
        for member in groupmembers:
            # Skip duplicates
            if member in groups:
                continue
            # Add member and its children
            if self.hasgroup(member):
                new_members, new_groups = self.expand_group(member)
                groups.update(new_groups)
                members.update(new_members)
            else:
                members[member] = 1
        return members, groups

    def scandicts(self):
        """ scan all pages matching the dict / group regex and init the dictdict
        
        TODO: the pickle would be updated via an event handler
              and every process checks the pickle regularly
              before reading the cache, the writer has to acquire a writelock
        """
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
                cache = caching.CacheEntry(request, arena, key, scope='wiki', use_pickle=True)
                data = cache.content()
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
                # function - this make the page list about 10 times faster.
                dictpages = request.rootpage.getPageList(user='', filter=isdict)
                grouppages = request.rootpage.getPageList(user='', filter=isgroup)

                # remove old entries when dict or group page have been deleted,
                # add entries when pages have been added
                # use copies because the dicts are shared via cfg.cache.DICTS_DATA
                # and must not be modified
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
            self.expand_groups()
            cache = caching.CacheEntry(request, arena, key, scope='wiki', use_pickle=True)
            cache.update(data)

        # remember it (persistent environments)
        self.cfg.cache.DICTS_DATA = data

