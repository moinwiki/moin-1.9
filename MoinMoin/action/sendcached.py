# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Send a raw object from the caching system

    This can be used e.g. for all image generating extensions:
    E.g. a thumbnail generating extension just writes the thumbnails
    into the cache and emits <img src="sendcached_url"> to display them.
    sendcached_url is e.g.:
    ...?action=sendcached&key=somethingnonguessable

    The cache contains somethingnonguessable.meta with the http header data and
    somethingnonguessable.data with the raw file data.

    TODO:
    * add error handling
    * maybe use page local caching, not global:
      + smaller directories
      - but harder to clean
      - harder to backup data_dir

    @copyright: 2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import config, caching

# Do NOT get this directly from request.form or user would be able to read any cache!
sendcached_arena = 'sendcached'
sendcached_scope = 'wiki'
do_locking = False

def execute(pagename, request):
    key = request.form.get('key', [None])[0]
    meta_cache = caching.CacheEntry(request, sendcached_arena, key+'.meta',
                                    sendcached_scope, do_locking=do_locking, use_pickle=True)
    locals().update(meta_cache.content())
    # Expected from meta dict:
    # filename (unicode)
    # last_modified (str)
    # content_type (str)
    # content_disposition (str)
    # content_length (int)

    if request.if_modified_since == last_modified:
        request.emit_http_headers(["Status: 304 Not modified"])
    else:
        # TODO: fix the encoding here, plain 8 bit is not allowed according to the RFCs
        # There is no solution that is compatible to IE except stripping non-ascii chars
        filename = filename.encode(config.charset)

        # send headers
        request.emit_http_headers([
            'Content-Type: %s' % content_type,
            'Last-Modified: %s' % last_modified,
            'Content-Length: %d' % content_length,
            'Content-Disposition: %s; filename="%s"' % (content_disposition, filename),
        ])

        # send data
        data_cache = caching.CacheEntry(request, sendcached_arena, key+'.data',
                                        sendcached_scope, do_locking=do_locking)
        data_file = open(data_cache._filename(), 'rb')
        request.send_file(data_file)

