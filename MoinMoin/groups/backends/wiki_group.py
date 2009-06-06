# -*- coding: iso-8859-1 -*-
"""
MoinMoin - wiki group backend

The wiki group backend enables you to define groups on wiki pages.  To
find group pages, request.cfg.cache.page_group_regexact pattern is
used.  To find group members, it parses theses pages and extracts the
first level list (wiki markup).

@copyright: 2008 MoinMoin:ThomasWaldmann,
            2008 MoinMoin:MelitaMihaljevic
@license: GPL, see COPYING for details
"""

import re

from MoinMoin import caching, wikiutil
from MoinMoin.Page import Page

class Group(object):
    name = 'wiki'

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
                    self.group = cache.content()
                else:
                    raise caching.CacheError
            except caching.CacheError:
                # either cache does not exist, is erroneous or not uptodate: recreate it
                text = page.get_raw_body()
                self.group = set(self._parse_page(text))
                cache.update(self.group)
        else:
            # we have no such group
            raise KeyError

    def _expand_group(self, group_name):
        groups = self.request.groups
        expanded_groups = set(group_name)
        members = set()

        for member in groups[group_name]:
            if member not in expanded_groups and member in groups:
                expanded_groups.add(member)
                members.update(self._expand_group(member))
            else:
                members.add(member)
        return members

    def _parse_page(self, text):
        """
        Parse <group_name> page and return members.
        """
        groups = self.request.groups
        unexpanded_members = [match.group('member') for match in self.group_page_parse_re.finditer(text)]

        members = set()
        # Expand possible recursive groups
        for member in unexpanded_members:
            if member in groups:
                members.update(self._expand_group(member))
            else:
                members.add(member)

        return members

    def __contains__(self, name):
        """
        Check if name is a member of this group.
        """
        return name in self.group

    def __iter__(self):
        """
        Iterate over group members.
        """
        return iter(self.group)


class Backend(object):
    name = 'wiki'

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

