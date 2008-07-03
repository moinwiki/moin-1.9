# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests of sendcached functions

    @copyright: 2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, StringIO

from MoinMoin import caching
from MoinMoin.action import sendcached

from MoinMoin._tests import become_trusted, create_page, nuke_page

class TestSendCached:
    """ testing action sendcached """
    pagename = u"AutoCreatedSillyPageToTestAttachments"

    def test_put_cache_minimal(self):
        """Test if put_cache() works"""
        request = self.request
        key = 'nooneknowsit'
        data = "dontcare"
        url = sendcached.put_cache(request, key, data)

        assert key in url
        meta_cache = caching.CacheEntry(request,
                                        arena=sendcached.sendcached_arena,
                                        scope=sendcached.sendcached_scope,
                                        key=key+'.meta', use_pickle=True)
        last_modified, headers = meta_cache.content()
        assert last_modified.endswith(' GMT') # only a very rough check, it has used cache mtime as last_modified
        assert "Content-Type: application/octet-stream" in headers
        assert "Content-Length: %d" % len(data) in headers

    def test_put_cache_guess_ct_give_lm(self):
        """Test if put_cache() works, when we give filename (so it guesses content_type) and last_modified"""
        request = self.request
        key = 'nooneknowsit'
        filename = "test.png"
        data = "dontcare"
        url = sendcached.put_cache(request, key, data,
                                   filename=filename, last_modified=1)
        assert key in url

        meta_cache = caching.CacheEntry(request,
                                        arena=sendcached.sendcached_arena,
                                        scope=sendcached.sendcached_scope,
                                        key=key+'.meta', use_pickle=True)
        last_modified, headers = meta_cache.content()
        assert last_modified == 'Thu, 01 Jan 1970 00:00:01 GMT'
        assert "Content-Type: image/png" in headers
        assert "Content-Length: %d" % len(data) in headers

    def test_put_cache_file_like_data(self):
        """Test if put_cache() works when we give it a file like object for the content"""
        request = self.request
        key = 'nooneknowsit'
        filename = "test.png"
        data = "dontcareatall"
        data_file = StringIO.StringIO(data)
        url = sendcached.put_cache(request, key, data_file)

        assert key in url
        meta_cache = caching.CacheEntry(request,
                                        arena=sendcached.sendcached_arena,
                                        scope=sendcached.sendcached_scope,
                                        key=key+'.meta', use_pickle=True)
        last_modified, headers = meta_cache.content()
        assert last_modified.endswith(' GMT') # only a very rough check, it has used cache mtime as last_modified
        assert "Content-Type: application/octet-stream" in headers
        assert "Content-Length: %d" % len(data) in headers

        data_cache = caching.CacheEntry(request,
                                        arena=sendcached.sendcached_arena,
                                        scope=sendcached.sendcached_scope,
                                        key=key+'.data')
        cached = data_cache.content()
        assert data == cached

    def test_put_cache_complex(self):
        """Test if put_cache() works for a more complex, practical scenario:

           As 'source' we just use some random integer as count value.

           The 'rendered representation' of it is just the word "spam" repeated
           count times, which we cache.

           The cache key calculation (for the 'non-guessable' keys) is also
           rather simple.

           In real world, source would be likely some big image, rendered
           representation of it a thumbnail / preview of it. Or some LaTeX
           source and its rendered representation as png image.
           Key calculation could be some MAC or some other hard to guess and
           unique string.
        """
        import random
        request = self.request
        render = lambda data: "spam" * data
        secret = 4223
        keycalc = lambda data: str(data * secret)

        source = random.randint(1, 100)
        rendered1 = render(source)
        key1 = keycalc(source)

        url1 = sendcached.put_cache(request, key1, rendered1)
        assert 'key=%s' % key1 in url1

        data_cache = caching.CacheEntry(request,
                                        arena=sendcached.sendcached_arena,
                                        scope=sendcached.sendcached_scope,
                                        key=key1+'.data')
        cached1 = data_cache.content()

        assert render(source) == cached1
        # if that succeeds, we have stored the rendered representation of source in the cache under key1

        # now we use some different source, render it and store it in the cache
        source = source * 2
        rendered2 = render(source)
        key2 = keycalc(source)

        url2 = sendcached.put_cache(request, key2, rendered2)
        assert 'key=%s' % key2 in url2

        data_cache = caching.CacheEntry(request,
                                        arena=sendcached.sendcached_arena,
                                        scope=sendcached.sendcached_scope,
                                        key=key2+'.data')
        cached2 = data_cache.content()

        assert render(source) == cached2
        # if that succeeds, we have stored the rendered representation of updated source in the cache under key2

        assert url2 != url1  # URLs must be different for different source (implies different keys)


coverage_modules = ['MoinMoin.action.sendcached']

