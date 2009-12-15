# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - DataBrowserWidget

    @copyright: 2002 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.widget import base
from MoinMoin import wikiutil

class DataBrowserWidget(base.Widget):

    def __init__(self, request, show_header=True, **kw):
        _ = request.getText
        base.Widget.__init__(self, request, **kw)
        self.data = None
        self.unqual_data_id = 'dbw.'
        self.data_id = request.formatter.qualify_id(self.unqual_data_id)
        # prefixed with __ are untranslated and to be used in the JS
        self._all = _('[all]')
        self.__all = '[all]'
        self._notempty = _('[not empty]')
        self.__notempty = '[notempty]'
        self._empty = _('[empty]')
        self.__empty = '[empty]'
        self._filter = _('filter')
        self.__filter = 'filter'
        self._show_header = show_header

    def setData(self, dataset):
        """ Sets the data for the browser (see MoinMoin.util.dataset).

        @param dataset: dataset containing either ascii, unicode or tuples.
                        If a dataset entry contains a tuple then the first
                        item in the tuple is displayed and the second item
                        is used for autofilters.
        """
        self.data = dataset
        if dataset.data_id:
            self.unqual_data_id = 'dbw.%s.' % dataset.data_id
            self.data_id = self.request.formatter.qualify_id(self.unqual_data_id)

    def _name(self, elem):
        """ return name tag for a HTML element
        @param elem: element name, will be prefixed by data id
        """
        return 'name="%s%s"' % (self.data_id, elem)

    def _makeoption(self, item, selected, ntitem=None):
        """ create an option for a <select> form element
        @param item: string containing the item name to show
        @param selected: indicates whether the item should be default or not
        """
        if selected:
            selected = ' selected'
        else:
            selected = ''
        assert(isinstance(item, basestring))
        if ntitem is None:
            ntitem = item
        return '<option value="%s"%s>%s</option>' % (
            wikiutil.escape(ntitem, True),
            selected,
            wikiutil.escape(item))

    def _filteroptions(self, idx):
        """ create options for all elements in the column
            given by idx
        """
        self.data.reset()
        row = self.data.next()
        # [empty] is a special already
        unique = ['']

        value = None
        name = '%sfilter%d' % (self.data_id, idx)
        if name in self.request.values:
            value = self.request.values.getlist(name)
        while row:
            option = row[idx]
            if isinstance(option, tuple):
                option = option[1]
            if not option in unique:
                unique.append(option)
            row = self.data.next()

        # fill in the empty field we left blank
        del unique[0]
        unique.sort()
        result = [self._makeoption(item, item == value) for item in unique]
        common = []
        common.append(self._makeoption(self._all, value == self.__all, self.__all))
        if '' in unique:
            common.extend([
                self._makeoption(self._empty, value == self.__empty, self.__empty),
                self._makeoption(self._notempty, value == self.__notempty, self.__notempty),
            ])
        return '\n'.join(common + result)

    def _format(self, formatter=None, method=None):
        """
        does the formatting of the table
        @param formatter: formatter
        @param method: None is the default and does not create a form
                       while "GET" or "POST" will create the form using the given method
        """
        fmt = formatter or self.request.formatter

        result = []
        if method:
            result.append(fmt.rawHTML('<form action="%s/%s" method="%s" name="%sform">' % (self.request.script_root, wikiutil.quoteWikinameURL(self.request.page.page_name), method, self.data_id)))
        result.append(fmt.div(1))

        havefilters = False
        for col in self.data.columns:
            if col.autofilter:
                havefilters = True
                break
        if havefilters:
            result.append(fmt.rawHTML('<input type="submit" value="%s" %s>' % (self._filter, self._name('submit'))))

        result.append(fmt.table(1, id='%stable' % self.unqual_data_id))

        # add header line
        if self._show_header:
            result.append(fmt.table_row(1))
            for idx in range(len(self.data.columns)):
                col = self.data.columns[idx]
                if col.hidden:
                    continue
                cell_attrs = {'class': 'hcolumn%d' % idx}
                result.append(fmt.table_cell(1, cell_attrs))
                result.append(fmt.strong(1))
                result.append(col.label or col.name)
                result.append(fmt.strong(0))

                if col.autofilter:
                    result.append(fmt.linebreak(False))
                    select = '<select %s onchange="dbw_update_search(\'%s\');">%s</select>' % (
                                      self._name('filter%d' % idx),
                                      self.data_id,
                                      self._filteroptions(idx))
                    result.append(fmt.rawHTML(select))

                result.append(fmt.table_cell(0))
            result.append(fmt.table_row(0))

        # add data
        self.data.reset()
        row = self.data.next()
        if row is not None:
            filters = [None] * len(row)

            if havefilters:
                for idx in range(len(row)):
                    name = '%sfilter%d' % (self.data_id, idx)
                    if name in self.request.values:
                        filters[idx] = self.request.getlist(name)
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
                    cell_attrs = {'class': 'column%d' % idx}
                    if isinstance(row[idx], tuple):
                        result.append(fmt.table_cell(1, cell_attrs, abbr=unicode(row[idx][1])))
                        result.append(unicode(row[idx][0]))
                    else:
                        result.append(fmt.table_cell(1, cell_attrs))
                        result.append(unicode(row[idx]))
                    result.append(fmt.table_cell(0))
                result.append(fmt.table_row(0))

            row = self.data.next()

        result.append(fmt.table(0))
        result.append(fmt.div(0))
        if method:
            result.append(fmt.rawHTML('</form>'))
        return ''.join(result)

    format = _format # DEPRECATED, use render()

    render = _format # Note: in moin <= 1.7.1 render() used request.write(), this was wrong!
                     # Now it just returns the result, as the other widgets do.

