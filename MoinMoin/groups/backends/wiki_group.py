# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - wiki_group backend provides access to the group definitions on a wiki pages.

    @copyright: 2003-2007 MoinMoin:ThomasWaldmann,
                2003 by Gustavo Niemeyer
                2009 MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""
import re, time

from MoinMoin import caching, Page
from MoinMoin.wikidicts import DictBase, DictDict

# Version of the internal data structure which is pickled.
# Please increment if you have changed the structure.
DICTS_PICKLE_VERSION = 6

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

class Backend(DictDict):
    """
    a dictionary of Group objects

    Config:
         cfg.page_group_regex
            Default: ".*Group$"

    XXX Group expanding. Groups should be expanded in the
        initialization, of the backend (which probably bad idea,
        because all groups may take a lot of memory, or expanded when
        needed. This must be transparent outside of the class.

    XXX Some methods were deleted (has_member, hasgroup), load_dicts
        was renamed to load_cache, scan_dicts to update_cache methods
        of super-class may be used somewhere in the code.
    """

    def __init__(self, request):
        self.cfg = request.cfg
        self.request = request

        # XXX probably, not the best place
        self.update_cache()

    def reset(self):
        self.dictdict = {}
        self.groupdict = {} # unexpanded groups
        self.picklever = DICTS_PICKLE_VERSION
        self.disk_cache_id = None

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

    def __contains__(self, groupname):
        """
        Check if group groupname is defined in some wikipage.
        """
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
            if member in self:
                new_members, new_groups = self.expand_group(member)
                groups.update(new_groups)
                members.update(new_members)
            else:
                members[member] = 1
        return members, groups

    def load_cache(self):
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

    def update_cache(self):
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
