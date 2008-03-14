# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Hits Macro

    This macro is used to show the cumulative hits of the wikipage where the Macro is called from.
    Optionally you could count how much this page or all pages were changed or viewed.

    <<Hits([all=(0,1)],[filter=(VIEWPAGE,SAVEPAGE)>>

        all: if set to 1/True/yes then cumulative hits over all wiki pages is returned.
             Default is 0/False/no.
        filter: if set to SAVEPAGE then the saved pages are counted. Default is VIEWPAGE.

   @copyright: 2004-2007 MoinMoin:ReimarBauer,
               2005 BenjaminVrolijk
   @license: GNU GPL, see COPYING for details.
"""

Dependencies = ['time'] # do not cache

from MoinMoin.logfile import eventlog


def macro_Hits(macro, all=False, filter=(u'VIEWPAGE', u'SAVEPAGE')):
    this_page = macro.formatter.page.page_name
    event_log = eventlog.EventLog(macro.request)
    event_log.set_filter([str(filter)])
    count = 0
    for event in event_log.reverse():
        pagename = event[2].get('pagename')
        if all or pagename == this_page:
            count += 1

    return u'%d' % count
