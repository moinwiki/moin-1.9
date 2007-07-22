# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Hits Macro

    This macro is used to show the cumulative hits of the wikipage where the Macro is called from.
    Optionally you could count how much this page or all pages were changed or viewed.

    [[Hits([all=(0,1)],[filter=(VIEWPAGE,SAVEPAGE)]]

        all: if set to 1/True/yes then cumulative hits over all wiki pages is returned.
             Default is 0/False/no.
        filter: if set to SAVEPAGE then the saved pages are counted. Default is VIEWPAGE.

   @copyright: 2004-2007 MoinMoin:ReimarBauer,
               2005 BenjaminVrolijk
   @license: GNU GPL, see COPYING for details.
"""

Dependencies = ['time'] # do not cache

from MoinMoin import wikiutil
from MoinMoin.logfile import eventlog


def macro_Hits(macro, all=None, filter=None):
    request = macro.request
    _ = request.getText
    this_page = macro.formatter.page.page_name
    event_filter = str(wikiutil.get_unicode(request, filter, 'filter', u'VIEWPAGE'))
    filters_possible = ('VIEWPAGE', 'SAVEPAGE')
    if not event_filter in filters_possible:
        raise ValueError(_("filter argument must be one of %s") % (', '.join(filters_possible)))
    count_all_pages = wikiutil.get_bool(request, all, 'all', False)

    event_log = eventlog.EventLog(request)
    event_log.set_filter([event_filter])
    count = 0
    for event in event_log.reverse():
        pagename = event[2].get('pagename')
        if count_all_pages or pagename == this_page:
            count += 1

    return u'%d' % count

