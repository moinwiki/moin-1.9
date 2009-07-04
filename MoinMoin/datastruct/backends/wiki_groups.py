# -*- coding: iso-8859-1 -*-
"""
MoinMoin - wiki group backend

The wiki group backend enables you to define groups on wiki pages.  To
find group pages, request.cfg.cache.page_group_regexact pattern is
used.  To find group members, it parses these pages and extracts the
first level list (wiki markup).

@copyright: 2008 MoinMoin:ThomasWaldmann,
            2008 MoinMoin:MelitaMihaljevic,
            2009 MoinMoin:DmitrijsMilajevs
@license: GPL, see COPYING for details
"""

import re

from MoinMoin import caching, wikiutil
from MoinMoin.Page import Page
from MoinMoin.datastruct.backends import BaseGroup, BaseGroupsBackend, GroupDoesNotExistError


class WikiGroup(BaseGroup):

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
                    return cache.content()
                else:
                    raise caching.CacheError
            except caching.CacheError:
                # either cache does not exist, is erroneous or not uptodate: recreate it
                members, member_groups = super(WikiGroup, self)._load_group()
                cache.update((members, member_groups))
                return members, member_groups
        else:
            raise GroupDoesNotExistError(group_name)


class WikiGroups(BaseGroupsBackend):

    def __contains__(self, group_name):
        return self.is_group(group_name) and Page(self.request, group_name).exists()

    def __iter__(self):
        return iter(self.request.rootpage.getPageList(user='', filter=self.page_group_regex.search))

    def __getitem__(self, group_name):
        return WikiGroup(request=self.request, name=group_name, backend=self)

    # * Member - ignore all but first level list items, strip
    # whitespace, strip free links markup. This is used for parsing
    # pages in order to find group page members.
    _group_page_parse_regex = re.compile(ur'^ \* +(?:\[\[)?(?P<member>.+?)(?:\]\])? *$', re.MULTILINE | re.UNICODE)

    def _retrieve_members(self, group_name):
        page = Page(self.request, group_name)
        text = page.get_raw_body()
        return [match.group('member') for match in self._group_page_parse_regex.finditer(text)]

