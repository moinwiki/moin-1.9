# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Hits Macro

    This macro is used to show the cummulative hits of the wikipage where the Macro is called from.
    Optional you could count how much this or all pages was changed or viewed.

    [[Hits([all=(0,1)],[filter=(VIEWPAGE,SAVEPAGE)]]

        all: if set to 1 then cummulative hits over all wiki pages is returned. Default is 0
        filter: if set to SAVEPAGE then the saved pages are counted. Default is VIEWPAGE.
    
   @copyright: 2004-2007 MoinMoin:ReimarBauer
               2005 BenjaminVrolijk
   @license: GNU GPL, see COPYING for details.
"""
Dependencies = ['time'] # do not cache

from MoinMoin import wikiutil
from MoinMoin.logfile import eventlog

class Hits:
    def __init__(self, macro, args):
        self.macro = macro
        self.request = macro.request
        self.formatter = macro.formatter
        argParser = wikiutil.ParameterParser("%(all)s%(filter)s")
        try:
            self.arg_list, self.arg_dict = argParser.parse_parameters(args)
        except ValueError:
            # TODO Set defaults until raise in ParameterParser.parse_parameters is changed
            self.arg_dict = {}
            self.arg_dict["filter"] = None
            self.arg_dict["all"] = 0

        self.count = 0

    def renderInText(self):
        return self.formatter.text("%s" % (self.getHits()))

    def getHits(self):
        formatter = self.macro.formatter
        kw = self.arg_dict
        if not kw["filter"]: kw["filter"] = "VIEWPAGE"

        event_log = eventlog.EventLog(self.request)
        event_log.set_filter([kw["filter"]])
        for event in event_log.reverse():
            pagename = event[2].get('pagename', None)
            if not kw["all"]:
                if pagename == formatter.page.page_name:
                   self.count += 1
            else:
                self.count += 1

        return self.count

def execute(macro, args):
    """ Temporary glue code to use with moin current macro system """
    return Hits(macro, args).renderInText()

