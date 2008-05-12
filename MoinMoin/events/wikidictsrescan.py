# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - wikidicts notification plugin for event system

    When a Group or Dict page changes, we rescan them and recreate the cache.

    @copyright: 2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import events as ev
from MoinMoin import wikidicts

def handle(event):
    # "changed" includes creation, deletion, renamed and copied
    if (isinstance(event, ev.PageChangedEvent) or isinstance(event, ev.PageRenamedEvent) or
        isinstance(event, ev.PageCopiedEvent) or isinstance(event, ev.TrivialPageChangedEvent)):
        cfg = event.request.cfg
        pagename = event.page.page_name
        if cfg.cache.page_dict_regexact.search(pagename) or \
           cfg.cache.page_group_regexact.search(pagename):
            return handle_groupsdicts_changed(event)


def handle_groupsdicts_changed(event):
    """ Handles events related to groups and dicts page changes:
        Scans all pages matching the dict / group regex and pickles the
        data to disk.
    """
    request = event.request
    page = event.page

    logging.debug("groupsdicts changed: %r, scan_dicts started", page.page_name)
    del request.dicts
    gd = wikidicts.GroupDict(request)
    gd.scan_dicts()
    logging.debug("groupsdicts changed: scan_dicts finished")

