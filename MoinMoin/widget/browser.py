# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - DataBrowserWidget

    @copyright: 2002 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.widget import base
from MoinMoin import wikiutil

class DataBrowserWidget(base.Widget):

    def __init__(self, request, **kw):
        _ = request.getText
        base.Widget.__init__(self, request, **kw)
        self.data = None
        self.data_id = 'dbw.'
        self._all = _('[all]')
        self._notempty = _('[not empty]')
        self._empty = _('[empty]')
        self._filter = _('filter')

    def setData(self, dataset):
        """ Sets the data for the browser (see MoinMoin.util.dataset).

        @param dataset: dataset containing either ascii, unicode or tuples.
                        If a dataset entry contains a tuple then the first
                        item in the tuple is displayed and the second item
                        is used for autofilters.
        """
        self.data = dataset
        if dataset.data_id:
            self.data_id = 'dbw.%s.' % dataset.data_id

    def _name(self, elem):
        """ return name tag for a HTML element
        @param elem: element name, will be prefixed by data id
        """
        return 'name="%s%s"' % (self.data_id, elem)

    def _makeoption(self, item, selected):
        """ create an option for a <select> form element
        @param item: string containing the item name to show
        @param selected: indicates whether the item should be default or not
        """
        if selected:
            selected = ' selected'
        else:
            selected = ''
        assert(isinstance(item, basestring))
        item = wikiutil.escape(item)
        return '<option value="%s"%s>%s</option>' % (item, selected, item)

    def _filteroptions(self, idx):
        """ create options for all elements in the column
            given by idx
        """
        self.data.reset()
        row = self.data.next()
        # leave the 'empty' slot blank so we avoid adding
        # blank items when getting all possibilities
        unique = [self._all, '', self._notempty]

        value = None
        name = '%sfilter%d' % (self.data_id, idx)
        if name in self.request.form:
            value = self.request.form[name][0]
        while row:
            option = row[idx]
            if isinstance(option, tuple):
                option = option[1]
            if not option in unique:
                unique.append(option)
            row = self.data.next()

        # fill in the empty field we left blank
        unique[1] = self._empty
        sorted = unique[3:]
        sorted.sort()
        unique = unique[:3] + sorted
        return '\n'.join([self._makeoption(item, item == value) for item in unique])

    def format(self):
        fmt = self.request.formatter

        result = []
        result.append(fmt.rawHTML('<form action="" method="GET">'))
        result.append(fmt.div(1))

        havefilters = False
        for col in self.data.columns:
            if col.autofilter:
                havefilters = True
                break
        if havefilters:
            result.append(fmt.rawHTML('<input type="submit" value="%s" %s>' % (self._filter, self._name('submit'))))

        result.append(fmt.table(1))

        # add header line
        result.append(fmt.table_row(1))
        for idx in range(len(self.data.columns)):
            col = self.data.columns[idx]
            if col.hidden: continue
            result.append(fmt.table_cell(1))
            result.append(fmt.strong(1))
            result.append(col.label or col.name)
            result.append(fmt.strong(0))

            if col.autofilter:
                result.append(fmt.linebreak(False))
                select = '<select %s>%s</select>' % (self._name('filter%d' % idx),
                                                     self._filteroptions(idx))
                result.append(fmt.rawHTML(select))

            result.append(fmt.table_cell(0))
        result.append(fmt.table_row(0))

        # add data
        self.data.reset()
        row = self.data.next()
        filters = [None] * len(row)

        if havefilters:
            for idx in range(len(row)):
                name = '%sfilter%d' % (self.data_id, idx)
                if name in self.request.form:
                    filters[idx] = self.request.form[name][0]
                    if filters[idx] == self._all:
                        filters[idx] = None

        while row:
            hidden = False

            if havefilters:
                # check if row needs to be hidden due to filtering
                for idx in range(len(row)):
                    if filters[idx]:
                        if isinstance(row[idx], tuple):
                            data = unicode(row[idx][1])
                        else:
                            data = unicode(row[idx])
                        if data != '' and filters[idx] == self._notempty:
                            continue
                        if data == '' and filters[idx] == self._empty:
                            continue
                        if data != filters[idx]:
                            hidden = True
                            break

            if not hidden:
                result.append(fmt.table_row(1))
                for idx in range(len(row)):
                    if self.data.columns[idx].hidden:
                        continue
                    result.append(fmt.table_cell(1))
                    if isinstance(row[idx], tuple):
                        result.append(unicode(row[idx][0]))
                    else:
                        result.append(unicode(row[idx]))
                    result.append(fmt.table_cell(0))
                result.append(fmt.table_row(0))

            row = self.data.next()

        result.append(fmt.table(0))
        result.append(fmt.div(0))
        result.append(fmt.rawHTML('</form>'))
        return ''.join(result)

    toHTML = format # old name of "format" function DEPRECATED, will be removed in 1.7

    def render(self):
        self.request.write(self.format())

