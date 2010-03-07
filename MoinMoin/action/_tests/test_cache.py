# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests of cache action functions

    @copyright: 2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, StringIO

from MoinMoin import caching
from MoinMoin.action import AttachFile, cache

from MoinMoin._tests import become_trusted, create_page, nuke_page

class TestSendCached:
    """ testing action cache """
    pagename = u"AutoCreatedSillyPageToTestAttachments"

    def test_cache_key_content(self):
        request = self.request
        result1 = cache.key(request, content='foo', secret='bar')
        result2 = cache.key(request, content='foo', secret='baz')
        assert result1  # not empty
        assert result1 != result2  # different for different secret
        result3 = cache.key(request, content='foofoo', secret='baz')
        assert result3 != result2  # different for different content
        result4 = cache.key(request, content='foo'*1000, secret='baz')
        assert len(result4) == len(result3)  # same length of key for different input lengths

    def test_cache_key_attachment(self):
        request = self.request
        pagename = self.pagename
        attachname = 'foo.txt'

        become_trusted(request)
        create_page(request, pagename, u"Foo!")

        AttachFile.add_attachment(request, pagename, attachname, "Test content1", True)

        result1 = cache.key(request, itemname=pagename, attachname=attachname, secret='bar')
        result2 = cache.key(request, itemname=pagename, attachname=attachname, secret='baz')
        assert result1  # not empty
        assert result1 != result2  # different for different secret

        # test below does not work, because mtime is often same, inode can be same due to how add_attachment
        # works, file size is same, attachment name is same, wikiname/pagename is same.
        # In practice, this should rather rarely cause problems:
        #AttachFile.add_attachment(request, pagename, attachname, "Test content2", True)
        #result3 = cache.key(request, itemname=pagename, attachname=attachname, secret='baz')
        #assert result3 != result2  # different for different content

        AttachFile.add_attachment(request, pagename, attachname, "Test content33333", True)
        result4 = cache.key(request, itemname=pagename, attachname=attachname, secret='baz')
        assert len(result4) == len(result2)  # same length of key for different input lengths
        nuke_page(request, pagename)

    def test_put_cache_minimal(self):
        """Test if put_cache() works"""
        request = self.request
        key = 'nooneknowsit'
        data = "dontcare"
        cache.put(request, key, data)
        url = cache.url(request, key)

        assert key in url
        meta_cache = caching.CacheEntry(request,
                                        arena=cache.cache_arena,
                                        scope=cache.cache_scope,
                                        key=key+'.meta', use_pickle=True)
        meta = meta_cache.content()
        assert meta['httpdate_last_modified'].endswith(' GMT') # only a very rough check, it has used cache mtime as last_modified
        assert ("Content-Type", "application/octet-stream") in meta['headers']
        assert ("Content-Length", len(data)) in meta['headers']

    def test_put_cache_guess_ct_give_lm(self):
        """Test if put_cache() works, when we give filename (so it guesses content_type) and last_modified"""
        request = self.request
        key = 'nooneknowsit'
        filename = "test.png"
        data = "dontcare"
        cache.put(request, key, data, filename=filename, last_modified=1)
        url = cache.url(request, key)
        assert key in url

        meta_cache = caching.CacheEntry(request,
                                        arena=cache.cache_arena,
                                        scope=cache.cache_scope,
                                        key=key+'.meta', use_pickle=True)
        meta = meta_cache.content()
        assert meta['httpdate_last_modified'] == 'Thu, 01 Jan 1970 00:00:01 GMT'
        assert ("Content-Type", "image/png") in meta['headers']
        assert ("Content-Length", len(data)) in meta['headers']

    def test_put_cache_file_like_data(self):
        """Test if put_cache() works when we give it a file like object for the content"""
        request = self.request
        key = 'nooneknowsit'
        filename = "test.png"
        data = "dontcareatall"
        data_file = StringIO.StringIO(data)
        cache.put(request, key, data_file)
        url = cache.url(request, key)

        assert key in url
        meta_cache = caching.CacheEntry(request,
                                        arena=cache.cache_arena,
                                        scope=cache.cache_scope,
                                        key=key+'.meta', use_pickle=True)
        meta = meta_cache.content()
        assert meta['httpdate_last_modified'].endswith(' GMT') # only a very rough check, it has used cache mtime as last_modified
        assert ("Content-Type", "application/octet-stream") in meta['headers']
        assert ("Content-Length", len(data)) in meta['headers']

        data_cache = caching.CacheEntry(request,
                                        arena=cache.cache_arena,
                                        scope=cache.cache_scope,
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

        cache.put(request, key1, rendered1)
        url1 = cache.url(request, key1)
        assert 'key=%s' % key1 in url1

        data_cache = caching.CacheEntry(request,
                                        arena=cache.cache_arena,
                                        scope=cache.cache_scope,
                                        key=key1+'.data')
        cached1 = data_cache.content()

        assert render(source) == cached1
        # if that succeeds, we have stored the rendered representation of source in the cache under key1

        # now we use some different source, render it and store it in the cache
        source = source * 2
        rendered2 = render(source)
        key2 = keycalc(source)

        cache.put(request, key2, rendered2)
        url2 = cache.url(request, key2)
        assert 'key=%s' % key2 in url2

        data_cache = caching.CacheEntry(request,
                                        arena=cache.cache_arena,
                                        scope=cache.cache_scope,
                                        key=key2+'.data')
        cached2 = data_cache.content()

        assert render(source) == cached2
        # if that succeeds, we have stored the rendered representation of updated source in the cache under key2

        assert url2 != url1  # URLs must be different for different source (implies different keys)


coverage_modules = ['MoinMoin.action.cache']

