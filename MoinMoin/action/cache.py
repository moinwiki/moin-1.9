# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Send a raw object from the caching system (and offer utility
    functions to put data into cache, calculate cache key, etc.).

    This can be used e.g. for all image generating extensions:
    E.g. a thumbnail generating extension just uses cache.put() to
    write the thumbnails into the cache and emits <img src="cache_url">
    to display them. cache_url is returned by put() or url().

    IMPORTANT: use some non-guessable key derived from your source content,
               use cache.key() if you don't have something better.

    TODO:
    * add secret to wikiconfig
    * add error handling
    * maybe use page local caching, not global:
      + smaller directories
      - but harder to clean
      - harder to backup data_dir
    * move file-like code to caching module
    * add auto-key generation?

    @copyright: 2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import hmac, sha

from MoinMoin import log
logging = log.getLogger(__name__)

# keep both imports below as they are, order is important:
from MoinMoin import wikiutil
import mimetypes

from MoinMoin import config, caching
from MoinMoin.util import filesys
from MoinMoin.action import AttachFile

action_name = 'cache'

# Do NOT get this directly from request.form or user would be able to read any cache!
cache_arena = 'sendcache'
cache_scope = 'wiki'
do_locking = False

def key(request, wikiname=None, itemname=None, attachname=None, content=None, secret=None):
    """
    Calculate a (hard-to-guess) cache key.

    If content is supplied, we will calculate and return a hMAC of the content.

    If wikiname, itemname, attachname is given, we don't touch the content (nor do
    we read it ourselves from the attachment file), but we just calculate a key
    from the given metadata values and some metadata we get from the filesystem.

    Hint: if you need multiple cache objects for the same source content (e.g.
          thumbnails of different sizes for the same image), calculate the key
          only once and then add some different prefixes to it to get the final
          cache keys.

    @param request: the request object
    @param wikiname: the name of the wiki (if not given, will be read from cfg)
    @param itemname: the name of the page
    @param attachname: the filename of the attachment
    @param content: content data as unicode object (e.g. for page content or
                    parser section content)
    """
    secret = secret or 'nobodyexpectedsuchasecret'
    if content:
        hmac_data = content
    elif itemname is not None and attachname is not None:
        wikiname = wikiname or request.cfg.interwikiname or request.cfg.siteid
        fuid = filesys.fuid(AttachFile.getFilename(request, itemname, attachname))
        hmac_data = u''.join([wikiname, itemname, attachname, repr(fuid)])
    else:
        raise AssertionError('cache_key called with unsupported parameters')

    hmac_data = hmac_data.encode('utf-8')
    key = hmac.new(secret, hmac_data, sha).hexdigest()
    return key


def put(request, key, data,
        filename=None,
        content_type=None,
        content_disposition=None,
        content_length=None,
        last_modified=None,
        bufsize=8192):
    """
    Put an object into the cache to send it with cache action later.

    @param request: the request object
    @param key: non-guessable key into cache (str)
    @param data: content data (str or open file-like obj)
    @param filename: filename for content-disposition header and for autodetecting
                     content_type (unicode, default: None)
    @param content_disposition: type for content-disposition header (str, default: None)
    @param content_type: content-type header value (str, default: autodetect from filename)
    @param last_modified: last modified timestamp (int, default: autodetect)
    @param content_length: data length for content-length header (int, default: autodetect)
    @return: URL of cached object
    """
    import os.path
    from MoinMoin.util import timefuncs

    if filename:
        # make sure we just have a simple filename (without path)
        filename = os.path.basename(filename)

        if content_type is None:
            # try autodetect
            mt, enc = mimetypes.guess_type(filename)
            if mt:
                content_type = mt

    if content_type is None:
        content_type = 'application/octet-stream'

    data_cache = caching.CacheEntry(request, cache_arena, key+'.data', cache_scope, do_locking=do_locking)
    data_cache_fname = data_cache._filename()

    if hasattr(data, 'read'):
        import shutil
        data_cache_file = open(data_cache_fname, 'wb')
        shutil.copyfileobj(data, data_cache_file)
        data_cache_file.close()
    else:
        data_cache.update(data)

    content_length = content_length or os.path.getsize(data_cache_fname)
    last_modified = last_modified or os.path.getmtime(data_cache_fname)

    last_modified = timefuncs.formathttpdate(int(last_modified))
    headers = ['Content-Type: %s' % content_type,
               'Last-Modified: %s' % last_modified,
               'Content-Length: %s' % content_length,
              ]
    if content_disposition and filename:
        # TODO: fix the encoding here, plain 8 bit is not allowed according to the RFCs
        # There is no solution that is compatible to IE except stripping non-ascii chars
        filename = filename.encode(config.charset)
        headers.append('Content-Disposition: %s; filename="%s"' % (content_disposition, filename))

    meta_cache = caching.CacheEntry(request, cache_arena, key+'.meta', cache_scope, do_locking=do_locking, use_pickle=True)
    meta_cache.update((last_modified, headers))

    return url(request, key, do='get')


def exists(request, key, strict=False):
    """
    Check if a cached object for this key exists.

    @param request: the request object
    @param key: non-guessable key into cache (str)
    @param strict: if True, also check the data cache, not only meta (bool, default: False)
    @return: is object cached? (bool)
    """
    if strict:
        data_cache = caching.CacheEntry(request, cache_arena, key+'.data', cache_scope, do_locking=do_locking)
        data_cached = data_cache.exists()
    else:
        data_cached = True  # we assume data will be there if meta is there

    meta_cache = caching.CacheEntry(request, cache_arena, key+'.meta', cache_scope, do_locking=do_locking, use_pickle=True)
    meta_cached = meta_cache.exists()

    return meta_cached and data_cached


def remove(request, key):
    """ delete headers/data cache for key """
    meta_cache = caching.CacheEntry(request, cache_arena, key+'.meta', cache_scope, do_locking=do_locking, use_pickle=True)
    meta_cache.remove()
    data_cache = caching.CacheEntry(request, cache_arena, key+'.data', cache_scope, do_locking=do_locking)
    data_cache.remove()


def url(request, key, do='get'):
    """ return URL for the object cached for key """
    return "%s/?%s" % (
        request.getScriptname(),
        wikiutil.makeQueryString(dict(action=action_name, do=do, key=key), want_unicode=False))


def _get_headers(request, key):
    """ get last_modified and headers cached for key """
    meta_cache = caching.CacheEntry(request, cache_arena, key+'.meta', cache_scope, do_locking=do_locking, use_pickle=True)
    last_modified, headers = meta_cache.content()
    return last_modified, headers


def _get_datafile(request, key):
    """ get an open data file for the data cached for key """
    data_cache = caching.CacheEntry(request, cache_arena, key+'.data', cache_scope, do_locking=do_locking)
    data_file = open(data_cache._filename(), 'rb')
    return data_file


def _do_get(request, key):
    """ send a complete http response with headers/data cached for key """
    last_modified, headers = _get_headers(request, key)
    if request.if_modified_since == last_modified:
        request.emit_http_headers(["Status: 304 Not modified"])
    else:
        request.emit_http_headers(headers)
        request.send_file(_get_datafile(request, key))


def _do_remove(request, key):
    """ delete headers/data cache for key """
    remove(request, key)
    request.emit_http_headers(["Status: 200 OK"])


def _do(request, do, key):
    if do == 'get':
        _do_get(request, key)
    elif do == 'remove':
        _do_remove(request, key)

def execute(pagename, request):
    do = request.form.get('do', [None])[0]
    key = request.form.get('key', [None])[0]
    _do(request, do, key)

