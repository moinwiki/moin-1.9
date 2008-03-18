# -*- coding: utf-8 -*-
"""
    MoinMoin - Parser for CSV data

    This parser uses the databrowser widget to display the data.

    It supports the following parser arguments:

     * delimiter/separator: the delimiter to use instead of ;
     * quotechar: quoting character, default off, must be ascii!
     * show: comma-separated list of columns to show only
     * hide: comma-separated list of columns to hide
     * autofilter: comma-separated list of columns to equip with
                   auto-filter drop down
     * name: name of the dataset
     * link: comma separated list of columns that take links, separate
             the link and the description with a space
     * static_cols: comma-separated list of columns that are static
                    and present in each row
     * static_vals: comma-separated list of values for those static
                    columns

    The static column feature is only really useful if the dataset
    postprocessed by some other plugin collecting data from multiple
    wiki pages.

    @copyright: 2007, 2008 Johannes Berg <johannes@sipsolutions.net>
    @license: GNU GPL, see COPYING for details.
"""

from csv import reader

from MoinMoin.util.dataset import TupleDataset, Column
from MoinMoin.widget.browser import DataBrowserWidget
from MoinMoin.wikiutil import escape


Dependencies = ['time']

class Parser:
    extensions = ['.csvdata']
    Dependencies = []

    def _read_rows(self, r):
        if self._first_row is not None:
            yield self._first_row
        for row in r:
            yield row

    def __init__(self, raw, request, **kw):
        self.request = request
        self._first_row = None
        formatter = request.formatter

        # workaround csv.reader deficiency by encoding to utf-8
        data = raw.encode('utf-8').split('\n')

        visible = None
        hiddenindexes = []
        hiddencols = []
        autofiltercols = []
        staticcols = []
        staticvals = []
        linkcols = []
        delimiter = ';'
        quotechar = '\x00' # can't be entered
        name = None
        hdr = reader([kw.get('format_args', '').strip().encode('utf-8')], delimiter=" ")
        args = hdr.next()

        for arg in args:
            arg = arg.decode('utf-8')
            try:
                key, val = arg.split('=', 1)
            except:
                # handle compatibility with original 'csv' parser
                if arg.startswith('-'):
                    try:
                        hiddenindexes.append(int(arg[1:]) - 1)
                    except ValueError:
                        pass
                else:
                    delimiter = arg.encode('utf-8')
                continue
            if key == 'separator' or key == 'delimiter':
                delimiter = val.encode('utf-8')
            if key == 'quotechar':
                if val == val.encode('utf-8'):
                    quotechar = val.encode('utf-8')
            elif key == 'show':
                visible = val.split(',')
            elif key == 'hide':
                hiddencols = val.split(',')
            elif key == 'autofilter':
                autofiltercols = val.split(',')
            elif key == 'name':
                name = val
            elif key == 'static_cols':
                staticcols = val.split(',')
            elif key == 'static_vals':
                staticvals = val.split(',')
            elif key == 'link':
                linkcols = val.split(',')

        if len(staticcols) > len(staticvals):
            staticvals.extend([''] * (len(staticcols)-len(staticvals)))
        elif len(staticcols) < len(staticvals):
            staticvals = staticvals[:len(staticcols)]

        r = reader(data, delimiter=delimiter, quotechar=quotechar)
        cols = map(lambda x: x.decode('utf-8'), r.next()) + staticcols

        self._show_header = True

        if cols == staticcols:
            try:
                self._first_row = map(lambda x: x.decode('utf-8'), r.next())
                cols = [None] * len(self._first_row) + staticcols
                self._show_header = False
            except StopIteration:
                pass

        num_entry_cols = len(cols) - len(staticcols)

        if not visible is None:
            for col in cols:
                if not col in visible:
                    hiddencols.append(col)

        linkparse = [False] * len(cols)

        data = TupleDataset(name)
        for colidx in range(len(cols)):
            col = cols[colidx]
            autofilter = col in autofiltercols
            hidden = col in hiddencols or colidx in hiddenindexes
            data.columns.append(Column(col, autofilter=autofilter, hidden=hidden))

            linkparse[colidx] = col in linkcols

        for row in self._read_rows(r):
            row = map(lambda x: x.decode('utf-8'), row)
            if len(row) > num_entry_cols:
                row = row[:num_entry_cols]
            elif len(row) < num_entry_cols:
                row.extend([''] * (num_entry_cols-len(row)))
            row += staticvals
            for colidx in range(len(row)):
                item = row[colidx]
                if linkparse[colidx]:
                    try:
                        url, item = item.split(' ', 1)
                        if url == '':
                            display = escape(item)
                        else:
                            display = ''.join([
                                formatter.url(1, url=url),
                                formatter.text(item),
                                formatter.url(0)])
                    except ValueError:
                        display = escape(item)
                else:
                    display = escape(item)
                row[colidx] = (display, item)
            data.addRow(tuple(row))
        self.data = data

    def format(self, formatter):
        browser = DataBrowserWidget(self.request, show_header=self._show_header)
        browser.setData(self.data)
        self.request.write(browser.format())
