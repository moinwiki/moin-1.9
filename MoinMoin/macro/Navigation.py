# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Navigation Macro

    @copyright: 2003 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re
from MoinMoin.Page import Page

Dependencies = ["namespace"]

# helpers
#!!! refactor these to an util module?
def _getParent(pagename):
    """ Return parent of pagename.
    """
    pos = pagename.rfind('/')
    if pos >= 0:
        return pagename[:pos]
    return None


def _getPages(request, filter_regex=None):
    """ Return a (filtered) list of pages names.
    """
    filter = None
    if filter_regex:
        filter = re.compile(filter_regex).match
    pages = request.rootpage.getPageList(filter=filter)
    pages.sort()
    return pages


def _getLinks(request, pagename, filter_regex=None):
    """ Return pagename for up, first, prev, next, last; each can be None.
    """
    pos, size, first, prev, next, last = 0, 0, None, None, None, None

    all_pages = _getPages(request, filter_regex)
    size = len(all_pages)

    if all_pages:
        try:
            pos = all_pages.index(pagename)
        except ValueError:
            # this should never happen in theory, but let's be sure
            pass
        else:
            if pos > 0:
                first = all_pages[0]
                prev = all_pages[pos-1]
            if pos+1 < len(all_pages):
                next = all_pages[pos+1]
                last = all_pages[-1]

    return pos, size, (first, prev, next, last)


class Navigation:
    """ Dispatcher class implementing the navigation schemes.
    """

    # querystring for slideshow links
    PROJECTION = {'action': 'print', 'media': 'projection', }

    def __init__(self, macro, args):
        """ Prepare common values used during processing.
        """
        self.macro = macro
        self.args = args.split(',')
        self._ = self.macro.request.getText

        self.pagename = self.macro.formatter.page.page_name
        self.print_mode = self.macro.request.action == 'print'
        self.media = self.macro.request.form.get('media', [None])[0]
        self.querystr = self.print_mode and self.PROJECTION or {}


    def dispatch(self):
        """ Return None if in plain print mode (no navigational
            elements in printouts), else the proper HTML code.
        """
        if self.print_mode and self.media != 'projection':
            return None

        scheme = self.args[0] or '<default>'
        return getattr(self, 'do_'+scheme, self.badscheme)()


    def badscheme(self):
        """ Bad scheme argument.
        """
        _ = self._
        scheme = self.args[0]
        return (self.macro.formatter.sysmsg(1) +
                self.macro.formatter.text(
            _("Unsupported navigation scheme '%(scheme)s'!") %
            {'scheme': scheme}) +
                self.macro.formatter.sysmsg(0))


    def do_children(self):
        """ Navigate to subpages from a parent page.
        """
        # delegate to siblings code, setting the parent explicitely
        return self.do_siblings(root=self.pagename)


    def do_siblings(self, root=None):
        """ Navigate from a subpage to its siblings.
        """
        _ = self._
        request = self.macro.request
        # get parent page name
        parent = root or _getParent(self.pagename)
        if not parent:
            return (self.macro.formatter.sysmsg(1) +
                    self.macro.formatter.text(_('No parent page found!'))+
                    self.macro.formatter.sysmsg(0))

        try:
            depth = int(self.args[1])
        except (IndexError, TypeError, ValueError):
            depth = 0

        # iterate over children, adding links to all of them
        result = []
        children = _getPages(request, '^%s/' % parent)
        for child in children:
            # display short page name, leaving out the parent path
            # (and make sure the name doesn't get wrapped)
            shortname = child[len(parent):]

            # possibly limit depth
            if depth and shortname.count('/') > depth:
                continue

            if child == self.pagename:
                # do not link to focus
                result.append(self.macro.formatter.text(shortname))
            else:
                # link to sibling / child
                result.append(Page(request, child).link_to(request, text=shortname, querystr=self.querystr))
            result.append(' &nbsp; ')

        return ''.join(result)


    def do_slideshow(self, focus=None):
        """ Slideshow master page links.

            If `focus` is set, it is the name of a slide page; these only
            get the mode toggle and edit links.
        """
        _ = self._
        curpage = focus or self.pagename
        result = []
        request = self.macro.request
        pg = Page(request, curpage)
        if self.print_mode:
            # projection mode
            label = _('Wiki')
            toggle = {}
            result.append(pg.link_to(request, text=_('Edit'), querystr={'action': 'edit'}))
            result.append(' &nbsp; ')
        else:
            # wiki mode
            label = _('Slideshow')
            toggle = self.PROJECTION

        # add mode toggle link
        result.append(pg.link_to(request, text=label, querystr=toggle))

        # leave out the following on slide pages
        if focus is None:
            children = _getPages(request, '^%s/' % self.pagename)
            if children:
                # add link to first child if one exists
                result.append(' &nbsp; ')
                result.append(Page(request, children[0]).link_to(request, text=_('Start'), querystr=self.querystr))

        return ''.join(result)


    def do_slides(self, root=None):
        """ Navigate within a slide show.
        """
        _ = self._
        request = self.macro.request
        parent = root or _getParent(self.pagename)
        if not parent:
            return (self.macro.formatter.sysmsg(1) +
                    self.macro.formatter.text(_('No parent page found!')) +
                    self.macro.formatter.sysmsg(0))

        # prepare link generation
        result = []
        labels = ['^', '|<', '<<', '>>', '>|']
        filter_regex = '^%s/' % re.escape(parent)
        pos, size, links = _getLinks(request, self.pagename, filter_regex)
        pos += 1
        links = zip(labels, (parent,) + links)

        # generate links to neighborhood
        for label, name in links:
            result.append(' ')
            if name:
                # active link
                result.append(Page(request, name).link_to(request, text=label, querystr=self.querystr))
            else:
                # ghosted link
                result.append(self.macro.formatter.text(label))
            result.append(' ')

            # position indicator in the middle
            if label == labels[2]:
                result.append(_('Slide %(pos)d of %(size)d') % {'pos': pos, 'size': size})

        return self.do_slideshow(focus=self.pagename) + ''.join(result)


def execute(macro, args):
    # get HTML code with the links
    navi = Navigation(macro, args or '').dispatch()

    if navi:
        # return links packed into a table
        return '<table class="navigation"><tr><td>%s</td></tr></table>' % navi

    # navigation disabled in plain print mode
    return ''

