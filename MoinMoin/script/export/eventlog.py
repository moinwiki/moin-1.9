# -*- coding: iso-8859-1 -*-
"""
MoinMoin - Dump event-log to CSV

@copyright: 2013 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

import sys
import csv

from MoinMoin import script
from MoinMoin.logfile.eventlog import EventLog


class PluginScript(script.MoinScript):
    """\
Purpose:
========
This tool allows you to dump a MoinMoin wiki event-log to CSV.

Detailed Instructions:
======================
General syntax: moin [options] export eventlog [eventlog-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

[eventlog-options] see below:
    To write into a file (default: stdout):
    --file=filename.csv
"""

    def __init__(self, argv=None, def_values=None):
        script.MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "-f", "--file", dest="csv_fname",
            help="CSV output filename [default: stdout]"
        )

    def mainloop(self):
        self.init_request()
        request = self.request

        if self.options.csv_fname:
            csv_file = open(self.options.csv_fname, "w")
        else:
            csv_file = sys.stdout

        columns = ['time', 'event', 'username', 'ip', 'wikiname', 'pagename', 'url', 'referrer', 'ua', ]
        csv_out = csv.DictWriter(csv_file, columns, restval='', extrasaction='ignore')
        for time, event, kv in EventLog(request):
            kv = kv.to_dict()  # convert from MultiDict to dict
            # convert usecs to secs
            time = time / 1000000.0
            # change some key names to simpler ones:
            ip = kv.pop('REMOTE_ADDR', '')
            ua = kv.pop('HTTP_USER_AGENT', '')
            referrer = kv.pop('HTTP_REFERER', '')
            kv.update(dict(time=unicode(time), event=event, ip=ip, referrer=referrer, ua=ua))
            # csv can't handle unicode, encode to utf-8:
            kv = dict([(k, v.encode('utf-8')) for k, v in kv.iteritems()])
            csv_out.writerow(kv)
        csv_file.close()

