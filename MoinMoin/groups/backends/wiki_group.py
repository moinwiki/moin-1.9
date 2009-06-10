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
from MoinMoin.groups.backends import BaseGroup, BaseBackend


class Group(BaseGroup):

    # * Member - ignore all but first level list items, strip
    # whitespace, strip free links markup. This is used for parsing
    # pages in order to find group page members
    group_page_parse_re = re.compile(ur'^ \* +(?:\[\[)?(?P<member>.+?)(?:\]\])? *$', re.MULTILINE | re.UNICODE)

    def _load_group(self):
        request = self.request
        group_name = self.name

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
            if self._backend.page_group_regex.match(member):
                member_groups.add(member)
            else:
                members_final.add(member)

        return members_final, member_groups


class Backend(BaseBackend):

    def __contains__(self, group_name):
        return self.page_group_regex.match(group_name) and Page(self.request, group_name).exists()

    def __iter__(self):
        return self.request.rootpage.getPageList(user='', filter=self.page_group_regex.search)

    def __getitem__(self, group_name):
        return Group(request=self.request, name=group_name, backend=self)

