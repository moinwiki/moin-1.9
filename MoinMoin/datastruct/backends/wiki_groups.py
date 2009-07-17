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

from MoinMoin import caching, wikiutil
from MoinMoin.Page import Page
from MoinMoin.datastruct.backends import GreedyGroup, BaseGroupsBackend, GroupDoesNotExistError
from MoinMoin.formatter.groups import Formatter


class WikiGroup(GreedyGroup):

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
        return self.is_group_name(group_name) and Page(self.request, group_name).exists()

    def __iter__(self):
        return iter(self.request.rootpage.getPageList(user='', filter=self.page_group_regex.search))

    def __getitem__(self, group_name):
        return WikiGroup(request=self.request, name=group_name, backend=self)

    def _retrieve_members(self, group_name):
        formatter = Formatter(self.request)
        page = Page(self.request, group_name, formatter=formatter)

        request_page = getattr(self.request, "page", None)
        self.request.page = page
        # send_special is set to True because acl of the page should
        # not be processed to avoid infinite recursion in the
        # following case.
        #
        # Consider page UserGroup content:
        #
        # #acl UserGroup:read,write,admin All:read
        #
        #  * ExampleUser
        #  * TestGroup
        #
        page.send_page(content_only=True, send_special=True)

        if request_page:
            self.request.page = request_page
        else:
            del self.request.page

        return formatter.members

