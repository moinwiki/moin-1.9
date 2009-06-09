# -*- coding: iso-8859-1 -*-
"""
MoinMoin - wiki group backend

The wiki group backend enables you to define groups on wiki pages.  To
find group pages, request.cfg.cache.page_group_regexact pattern is
used.  To find group members, it parses theses pages and extracts the
first level list (wiki markup).

@copyright: 2008 MoinMoin:ThomasWaldmann,
            2008 MoinMoin:MelitaMihaljevic,
            2009 MoinMoin:DmitrijsMilajevs
@license: GPL, see COPYING for details
"""

import re

from MoinMoin import caching, wikiutil
from MoinMoin.Page import Page


backend_type = "wiki"
backend_name= "wiki_group"


class Group(object):
    backend_type = backend_type
    backend_name = backend_name

    # * Member - ignore all but first level list items, strip
    # whitespace, strip free links markup. This is used for parsing
    # pages in order to find group page members
    group_page_parse_re = re.compile(ur'^ \* +(?:\[\[)?(?P<member>.+?)(?:\]\])? *$', re.MULTILINE | re.UNICODE)

    def __init__(self, request, group_name):
        """
        Initialize a wiki group.

        @parm request: request object
        @parm group_name: group name (== group page name)
        """
        self.request = request
        self.group_name = group_name
        self._load_group()

    def _load_group(self):
        request = self.request
        group_name = self.group_name

        page = Page(request, group_name)
        if page.exists():
            arena = 'pagegroups'
            key = wikiutil.quoteWikinameFS(group_name)
            cache = caching.CacheEntry(request, arena, key, scope='wiki', use_pickle=True)
            try:
                cache_mtime = cache.mtime()
                page_mtime = wikiutil.version2timestamp(page.mtime_usecs())
                # TODO: fix up-to-date check mtime granularity problems
                if cache_mtime > page_mtime:
                    # cache is uptodate
                    self.members, self.member_groups = cache.content()
                else:
                    raise caching.CacheError
            except caching.CacheError:
                # either cache does not exist, is erroneous or not uptodate: recreate it
                text = page.get_raw_body()
                self.members, self.member_groups = self._parse_page(text)
                cache.update((self.members, self. member_groups))
        else:
            raise KeyError("There is no such group page %s" % group_name)

    def _parse_page(self, text):
        """
        Parse <text> and return members and groups defined in the <text>
        """
        groups = self.request.groups

        text_members = (match.group('member') for match in self.group_page_parse_re.finditer(text))
        members_final = set()
        member_groups = set()

        for member in text_members:
            if self.request.cfg.cache.page_group_regexact.match(member):
                member_groups.add(member)
            else:
                members_final.add(member)

        return members_final, member_groups

    def _contains(self, member, processed_groups):
        """
        First check if <member> is part of this group and then check
        for every subgroup in this group.

        <processed_groups> is needed to avoid infinite recursion, if
        groups are defined recursively.

        @param member: member name [unicode]
        @param processed_groups: groups which were checked for containment before [set]
        """
        processed_groups.add(self.group_name)

        if member in self.members:
            return True
        else:
            groups = self.request.groups
            for group_name in self.member_groups:
                if group_name not in processed_groups and groups[group_name]._contains(member, processed_groups):
                    processed_groups.add(group_name)
                    return True

        return False

    def __contains__(self, member):
        """
        Check if <member> is defined in this group. Checks also for subgroups.
        """
        return self._contains(member, set())

    def _iter(self, yielded_members, processed_groups):
        """
        Iterate first over members of this group, then over subgroups of this group.

        <yielded_members> and <processed_groups> are needed to avoid infinite recursion.
        This can happen if there are two groups like these:
           OneGroup: Something, OtherGroup
           OtherGroup: OneGroup, SomethingOther

        @param yielded_members: members which have been already yielded before [set]
        @param processed_groups: group names which have been iterated before [set]
        """
        processed_groups.add(self.group_name)

        for member in self.members:
            if member not in yielded_members:
                yield member
                yielded_members.add(member)

        groups = self.request.groups
        for group_name in self.member_groups:
            if group_name not in processed_groups:
                for member in groups[group_name]._iter(yielded_members, processed_groups):
                    if member not in yielded_members:
                        yield member
                        yielded_members.add(member)


    def __iter__(self):
        """
        Iterate over members of this group. Iterates also over subgroups if any.
        """
        return self._iter(set(), set())

    def __repr__(self):
        return "<Group group_name=%s members=%s member_groups=%s>" %(self.group_name,
                                                                     self.members,
                                                                     self.member_groups)


class Backend(object):
    backend_type = backend_type
    backend_name = backend_name

    def __init__(self, request):
        """
        Create a group manager backend object.
        """
        self.request = request
        self.page_group_regex = request.cfg.cache.page_group_regexact

    def __contains__(self, group_name):
        """
        Check if there is group page <group_name>. <group_name> must satisfy page_group_regex.
        """
        return self.page_group_regex.match(group_name) and Page(self.request, group_name).exists()

    def __iter__(self):
        """
        Iterate over group names of groups available in the wiki.
        """
        grouppages = self.request.rootpage.getPageList(user='', filter=self.page_group_regex.search)
        return iter(grouppages)

    def __getitem__(self, group_name):
        """
        Return wiki group backend object.
        """
        return Group(self.request, group_name)

