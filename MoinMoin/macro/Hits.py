# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Hits Macro

    This macro is used to show the cummulative hits of the wikipage where the Macro is called from.
    Optional you could count how much this or all pages was changed or viewed.

    [[Hits([all=(0,1)],[filter=(VIEWPAGE,SAVEPAGE)]]

        all: if set to 1 then cummulative hits over all wiki pages is returned. Default is 0
        filter: if set to SAVEPAGE then the saved pages are counted. Default is VIEWPAGE.

   @copyright: 2004-2007 MoinMoin:ReimarBauer,
               2005 BenjaminVrolijk
   @license: GNU GPL, see COPYING for details.
"""

Dependencies = ['time'] # do not cache

from MoinMoin import wikiutil
from MoinMoin.logfile import eventlog

class Hits:
    def __init__(self, macro, args):
        self.request = macro.request
        self.formatter = macro.formatter
        self.this_page = macro.formatter.page.page_name
        argParser = wikiutil.ParameterParser("%(all)s%(filter)s")
        try:
            self.arg_list, self.arg_dict = argParser.parse_parameters(args)
            self.error = None
        except ValueError, err:
            self.error = str(err)

    def renderInText(self):
        if self.error:
            text = "Hits macro: %s" % self.error
        else:
            text = "%d" % self.getHits()
        return self.formatter.text(text)

    def getHits(self):
        event_filter = self.arg_dict["filter"]
        if not event_filter:
            event_filter = "VIEWPAGE"
        count_all_pages = self.arg_dict["all"]

        event_log = eventlog.EventLog(self.request)
        event_log.set_filter([event_filter])
        count = 0
        for event in event_log.reverse():
            pagename = event[2].get('pagename')
            if count_all_pages or pagename == self.this_page:
                count += 1

        return count

def execute(macro, args):
    """ Temporary glue code to use with moin current macro system """
    return Hits(macro, args).renderInText()

