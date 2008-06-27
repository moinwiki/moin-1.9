# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Send a raw object from the caching system

    This can be used e.g. for all image generating extensions:
    E.g. a thumbnail generating extension just uses sendcached.put_cache to
    write the thumbnails into the cache and emits <img src="sendcached_url">
    to display them. sendcached_url is returned by put_cache or get_url.

    IMPORTANT: use some non-guessable key derived from your source content.

    TODO:
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

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import config, caching

# keep both imports below as they are, order is important:
from MoinMoin import wikiutil
import mimetypes

action_name = 'sendcached'

# Do NOT get this directly from request.form or user would be able to read any cache!
sendcached_arena = action_name
sendcached_scope = 'wiki'
do_locking = False

def put_cache(request, key, data,
              filename=None,
              content_type=None,
              content_disposition=None,
              content_length=None,
              last_modified=None,
              bufsize=8192):
    """
    Cache an object to send with sendcached action later.

    @param request: the request object
    @param key: non-guessable key into sendcached cache (str)
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

    data_cache = caching.CacheEntry(request, sendcached_arena, key+'.data',
                                    sendcached_scope, do_locking=do_locking)
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

        headers.append(
               'Content-Disposition: %s; filename="%s"' % (content_disposition, filename)
        )

    meta_cache = caching.CacheEntry(request, sendcached_arena, key+'.meta',
                                    sendcached_scope, do_locking=do_locking, use_pickle=True)
    meta_cache.update((last_modified, headers))

    return get_url(request, key)


def get_url(request, key):
    return "%s/?%s" % (
        request.getScriptname(),
        wikiutil.makeQueryString(dict(action=action_name, key=key), want_unicode=False))


def execute(pagename, request):
    key = request.form.get('key', [None])[0]
    meta_cache = caching.CacheEntry(request, sendcached_arena, key+'.meta',
                                    sendcached_scope, do_locking=do_locking, use_pickle=True)
    last_modified, headers = meta_cache.content()

    if request.if_modified_since == last_modified:
        request.emit_http_headers(["Status: 304 Not modified"])
    else:
        request.emit_http_headers(headers)

        data_cache = caching.CacheEntry(request, sendcached_arena, key+'.data',
                                        sendcached_scope, do_locking=do_locking)
        data_file = open(data_cache._filename(), 'rb')
        request.send_file(data_file)

