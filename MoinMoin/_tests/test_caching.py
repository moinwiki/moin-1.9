# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.caching Tests

    @copyright: 2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py

import time

from MoinMoin import caching
from MoinMoin.PageEditor import PageEditor


class TestCaching(object):
    """ Tests the caching module """

    def test_persistence_simple(self):
        """ test if cache persists (on disk) """
        test_data = '12345abcde'
        cache = caching.CacheEntry(self.request, 'test_arena', 'test_key', 'wiki')
        cache.update(test_data)
        del cache
        cache = caching.CacheEntry(self.request, 'test_arena', 'test_key', 'wiki')
        assert test_data == cache.content()

    def test_persistence_pickle(self):
        """ test if cache persists (on disk), use pickle """
        test_data = {1: 2, 2: 3, 3: [4, 5, ], }
        cache = caching.CacheEntry(self.request, 'test_arena', 'test_key', 'wiki', use_pickle=True)
        cache.update(test_data)
        del cache
        cache = caching.CacheEntry(self.request, 'test_arena', 'test_key', 'wiki', use_pickle=True)
        assert test_data == cache.content()

    def test_persistence_encode(self):
        """ test if cache persists (on disk), use encoded string """
        test_data = u"üöäÜÖÄß"
        cache = caching.CacheEntry(self.request, 'test_arena', 'test_key', 'wiki', use_encode=True)
        cache.update(test_data)
        del cache
        cache = caching.CacheEntry(self.request, 'test_arena', 'test_key', 'wiki', use_encode=True)
        cache_data = cache.content()
        assert type(cache_data) == type(test_data)
        assert cache_data == test_data

    def test_mtime(self):
        """ test if cache mtime yields correct values """
        test_data = '12345abcde'
        now = time.time()
        cache = caching.CacheEntry(self.request, 'test_arena', 'test_key', 'wiki')
        cache.update(test_data)
        assert now - 2 <= cache.mtime() <= now + 2

    def test_remove(self):
        """ test if cache file removal works """
        cache = caching.CacheEntry(self.request, 'test_arena', 'test_key', 'wiki')
        assert cache.exists()
        cache.remove()
        assert not cache.exists()

    def test_update_needed(self):
        """ test update check) """
        test_data1 = u'does not matter'
        test_data2 = u'something else'
        page_name = u'Caching_TestPage'
        page = PageEditor(self.request, page_name)
        page._write_file(test_data1)
        cache = caching.CacheEntry(self.request, page, 'test_key', 'item')
        cache.update(test_data1)
        assert not cache.needsUpdate(page._text_filename())
        time.sleep(3) # XXX fails without, due to mtime granularity
        page = PageEditor(self.request, page_name)
        page._write_file(test_data2)
        assert cache.needsUpdate(page._text_filename())

    def test_filelike_readwrite(self):
        request = self.request
        key = 'nooneknowsit'
        arena = 'somethingfunny'
        data = "dontcare"
        cacheentry = caching.CacheEntry(request, arena, key, scope='wiki', do_locking=True,
                 use_pickle=False, use_encode=True)
        cacheentry.open(mode='w')
        cacheentry.write(data)
        cacheentry.close()

        assert cacheentry.exists()

        cacheentry.open(mode='r')
        rdata = cacheentry.read()
        cacheentry.close()

        assert data == rdata

coverage_modules = ['MoinMoin.caching']

