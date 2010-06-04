# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Dictionary / Group Functions

    @copyright: 2003-2007 MoinMoin:ThomasWaldmann,
                2003 by Gustavo Niemeyer
    @license: GNU GPL, see COPYING for details.
"""
import re, time

from MoinMoin import caching, Page

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

    # Regular expression used to parse text - subclass must override this
    regex = None  # re.compile(u'...', re.MULTILINE | re.UNICODE)

    def loadFromPage(self, request, name):
        """ load the dict from wiki page <name>'s content """
        self.name = name
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
    # Key:: Value - ignore all but key:: value pairs, strip whitespace, exactly one space after the :: is required
    regex = re.compile(ur'^ (?P<key>.+?):: (?P<val>.*?) *$', re.MULTILINE | re.UNICODE)

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

    If there are any free links using [[free link]] notation, the markup
    is stripped from the member.
    """
    # * Member - ignore all but first level list items, strip whitespace, strip free links markup
    regex = re.compile(ur'^ \* +(?:\[\[)?(?P<member>.+?)(?:\]\])? *$', re.MULTILINE | re.UNICODE)

    def __init__(self, request=None, pagename=None):
        self._list = []
        DictBase.__init__(self, request, pagename)

    def initFromText(self, text):
        for match in self.regex.finditer(text):
            member = match.group('member')
            self.addmember(member)

    def update(self, members):
        self.addmembers(members.keys())

    def __iter__(self):
        return iter(self._list)

    def members(self):
        """ return the group's members """
        return self._list[:]

    def addmembers(self, members):
        """ add a list of members to the group """
        for m in members:
            self.addmember(m)

    def addmember(self, member):
        """ add a member to the group """
        self[member] = 1
        self._list.append(member)

    def has_member(self, member):
        """ check if the group has member <member> """
        return self.has_key(member)

    def __repr__(self):
        return "<Group name=%r items=%r>" % (self.name, self._list)


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
        self.picklever = DICTS_PICKLE_VERSION
        self.disk_cache_id = None

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

    def load_dicts(self):
        """ load the dict from the cache """
        request = self.request
        rescan = False
        arena = 'wikidicts'
        key = 'dicts_groups'
        cache = caching.CacheEntry(request, arena, key, scope='wiki', use_pickle=True)
        current_disk_cache_id = cache.uid()
        try:
            self.__dict__.update(self.cfg.cache.DICTS_DATA)
            if (current_disk_cache_id is None or
                current_disk_cache_id != self.disk_cache_id):
                self.reset()
                raise AttributeError # not fresh, force load from disk
            else:
                return
        except AttributeError:
            try:
                data = cache.content()
                self.__dict__.update(data)
                self.disk_cache_id = current_disk_cache_id

                # invalidate the cache if the pickle version changed
                if self.picklever != DICTS_PICKLE_VERSION:
                    raise # force rescan
            except:
                self.reset()
                rescan = True

        if rescan:
            self.scan_dicts()
            self.load_dicts() # try again
            return

        data = {
            "disk_cache_id": self.disk_cache_id,
            "dictdict": self.dictdict,
            "groupdict": self.groupdict,
            "picklever": self.picklever
        }

        # remember it (persistent environments)
        self.cfg.cache.DICTS_DATA = data

    def scan_dicts(self):
        """ scan all pages matching the dict / group regex and
            cache the results on disk
        """
        request = self.request
        self.reset()

        # XXX get cache write lock here
        scan_begin_time = time.time()

        # Get all pages in the wiki - without user filtering using filter
        # function - this makes the page list about 10 times faster.
        isdict = self.cfg.cache.page_dict_regexact.search
        dictpages = request.rootpage.getPageList(user='', filter=isdict)
        for pagename in dictpages:
            self.adddict(request, pagename)

        isgroup = self.cfg.cache.page_group_regexact.search
        grouppages = request.rootpage.getPageList(user='', filter=isgroup)
        for pagename in grouppages:
            self.addgroup(request, pagename)

        scan_end_time = time.time()
        self.expand_groups()

        arena = 'wikidicts'
        key = 'dicts_groups'
        cache = caching.CacheEntry(request, arena, key, scope='wiki', use_pickle=True)
        data = {
            "scan_begin_time": scan_begin_time,
            "scan_end_time": scan_end_time,
            "dictdict": self.dictdict,
            "groupdict": self.groupdict,
            "picklever": self.picklever
        }
        cache.update(data)
        # XXX release cache write lock here
