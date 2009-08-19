# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - (re)building of Xapian indices

    @copyright: 2007 MoinMoin:KarolNowak
    @license: GNU GPL, see COPYING for details.
"""
import MoinMoin.events as ev

def handle_renamed(event):
    """Updates Xapian index when a page changes its name"""

    request = event.request

    if request.cfg.xapian_search:
        from MoinMoin.search.Xapian import Index
        index = Index(request)
        if index.exists():
            index.remove_item(event.old_page.page_name, now=0)
            index.update_page(event.page.page_name)


def handle_copied(event):
    """Updates Xapian index when a page is copied"""

    request = event.request

    if request.cfg.xapian_search:
        from MoinMoin.search.Xapian import Index
        index = Index(request)
        if index.exists():
            index.update_page(event.page.page_name)

def handle_changed(event, deleted=False):
    """Updates Xapian index when a page is changed"""

    request = event.request

    if request.cfg.xapian_search:
        from MoinMoin.search.Xapian import Index
        index = Index(request)
        if index.exists():
            if deleted:
                index.remove_item(event.page.page_name)
            else:
                index.update_page(event.page.page_name)


def handle_deleted(event):
    """Updates Xapian index when a page is deleted"""
    event = ev.PageChangedEvent(event.request, event.page, event.comment)
    handle_changed(event, deleted=True)


def handle_attached(event):
    """Updates Xapian index when a new attachment is added"""

    request = event.request

    if request.cfg.xapian_search:
        from MoinMoin.search.Xapian import Index
        index = Index(request)
        if index.exists():
            index.update_page(event.pagename)


def handle(event):
    if isinstance(event, ev.PageRenamedEvent):
        handle_renamed(event)
    elif isinstance(event, ev.PageCopiedEvent):
        handle_copied(event)
    elif isinstance(event, ev.PageChangedEvent) or isinstance(event, ev.TrivialPageChangedEvent):
        handle_changed(event)
    elif isinstance(event, ev.PageDeletedEvent):
        handle_deleted(event)
    elif isinstance(event, ev.FileAttachedEvent):
        handle_attached(event)
