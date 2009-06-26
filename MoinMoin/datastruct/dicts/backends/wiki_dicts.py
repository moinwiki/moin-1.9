# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WikiDict functions.

    @copyright: 2003-2007 MoinMoin:ThomasWaldmann,
                2003 by Gustavo Niemeyer
                2009 MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""
import re, time

from MoinMoin import caching, Page

# Version of the internal data structure which is pickled.
# Please increment if you have changed the structure.
DICTS_PICKLE_VERSION = 7


class WikiDict(dict):
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

    def __init__(self, request=None, pagename=None):
        dict.__init__(self)
        self.name = None
        if request is not None and pagename is not None:
            self._loadFromPage(request, pagename)

    def _loadFromPage(self, request, name):
        """ load the dict from wiki page <name>'s content """
        self.name = name
        text = Page.Page(request, name).get_raw_body()
        self._initFromText(text)

    def _initFromText(self, text):
        for match in self.regex.finditer(text):
            key, val = match.groups()
            self[key] = val

    def __repr__(self):
        return "<Dict name=%r items=%r>" % (self.name, self.items())


class WikiDicts:
    """ a dictionary of Dict objects

       Config:
           cfg.page_dict_regex
               Default: ".*Dict$"  Defs$ Vars$ ???????????????????
    """

    def __init__(self, request):
        self.cfg = request.cfg
        self.request = request

    def reset(self):
        self.dictdict = {}
        self.namespace_timestamp = 0
        self.pageupdate_timestamp = 0
        self.base_timestamp = 0
        self.picklever = DICTS_PICKLE_VERSION
        self.disk_cache_id = None

    def values(self, dictname):
        """ get values of dict <dictname> """
        try:
            d = self.dictdict[dictname]
        except KeyError:
            return []
        return d.values()

    def __getitem__(self, dictname):
        try:
            d = self.dictdict[dictname]
        except KeyError:
            return {}
        return d

    def _adddict(self, request, dictname):
        """ add a new dict (will be read from the wiki page) """
        self.dictdict[dictname] = WikiDict(request, dictname)

    def __contains__(self, dictname):
        return self.dictdict.has_key(dictname)

    def load_dicts(self):
        """ load the dict from the cache """
        request = self.request
        rescan = False
        arena = 'wikidicts'
        key = 'dicts'
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
            "picklever": self.picklever
        }

        # remember it (persistent environments)
        self.cfg.cache.DICTS_DATA = data

    def scan_dicts(self):
        """ scan all pages matching the dict regex and cache the
            results on disk
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
            self._adddict(request, pagename)

        scan_end_time = time.time()

        arena = 'wikidicts'
        key = 'dicts'
        cache = caching.CacheEntry(request, arena, key, scope='wiki', use_pickle=True)
        data = {
            "scan_begin_time": scan_begin_time,
            "scan_end_time": scan_end_time,
            "dictdict": self.dictdict,
            "picklever": self.picklever
        }
        cache.update(data)
        # XXX release cache write lock here


