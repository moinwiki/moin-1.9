# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Parser for CSV data

    This parser lacks to flexibility to read arbitary csv dialects.

    Perhaps this should be rewritten using another CSV lib
    because the standard module csv does not support unicode.

    @copyright: 2004 Oliver Graf <ograf@bitart.de>, Alexander Schremmer
    @license: GNU GPL, see COPYING for details.
"""

Dependencies = []

class Parser:
    """ Format CSV data as table
    """

    extensions = ['.csv']
    Dependencies = []

    def __init__(self, raw, request, **kw):
        """ Store the source text.
        """
        self.raw = raw
        self.request = request
        self.form = request.form
        self._ = request.getText

        # parse extra arguments for excludes
        self.exclude = []
        self.separator = ';'
        for arg in kw.get('format_args','').split():
            if arg[0] == '-':
                try:
                    idx = int(arg[1:])
                except ValueError:
                    pass
                else:
                    self.exclude.append(idx-1)
            else:
                self.separator = arg

    def format(self, formatter):
        """ Parse and send the table.
        """
        lines = self.raw.split('\n')
        if lines[0]:
            # expect column headers in first line
            first = 1
        else:
            # empty first line, no bold headers
            first = 0
            del lines[0]

        self.request.write(formatter.table(1))
        for line in lines:
            self.request.write(formatter.table_row(1))
            cells = line.split(self.separator)
            for idx in range(len(cells)):
                if idx in self.exclude:
                    continue
                self.request.write(formatter.table_cell(1))
                if first:
                    self.request.write(formatter.strong(1))
                self.request.write(formatter.text(cells[idx]))
                if first:
                    self.request.write(formatter.strong(0))
                self.request.write(formatter.table_cell(0))
            self.request.write(formatter.table_row(0))
            first = 0
        self.request.write(formatter.table(0))

