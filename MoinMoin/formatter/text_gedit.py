# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "text/html+css" Formatter for feeding the GUI editor

    @copyright: (c) Bastian Blank, Florian Festi, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.formatter import FormatterBase, text_html
from MoinMoin import wikiutil, config
from MoinMoin.Page import Page
from MoinMoin.action import AttachFile

class Formatter(text_html.Formatter):
    """ Send HTML data for the GUI editor """

    # Block elements ####################################################

    def heading(self, on, depth, **kw):
        # remember depth of first heading, and adapt counting depth accordingly
        if not self._base_depth:
            self._base_depth = depth

        count_depth = max(depth - (self._base_depth - 1), 1)
        heading_depth = depth + 1

        # closing tag, with empty line after, to make source more readable
        if not on:
            return self._close('h%d' % heading_depth)
        else:
            return self._open('h%d' % heading_depth, **kw)

    # Links ##############################################################

    def pagelink(self, on, pagename='', page=None, **kw):
        """ Link to a page.

            formatter.text_python will use an optimized call with a page!=None
            parameter. DO NOT USE THIS YOURSELF OR IT WILL BREAK.

            See wikiutil.link_tag() for possible keyword parameters.
        """
        apply(FormatterBase.pagelink, (self, on, pagename, page), kw)
        if page is None:
            page = Page(self.request, pagename, formatter=self)
        return page.link_to(self.request, on=on, **kw)

    def interwikilink(self, on, interwiki='', pagename='', **kw):
        """
        @keyword title: override using the interwiki wikiname as title
        """
        if not on:
            return self.url(0) # return '</a>'
        html_class = 'badinterwiki' # we use badinterwiki in any case to simplify reverse conversion
        href = wikiutil.quoteWikinameURL(pagename) or "/" # FCKeditor behaves strange on empty href
        title = kw.get('title', interwiki)
        return self.url(1, href, title=title, do_escape=1, css=html_class) # interwiki links with pages with umlauts

    def attachment_inlined(self, url, text, **kw):
        if url == text:
            return '<span style="background-color:#ffff11">inline:%s</span>' % url
        else:
            return '<span style="background-color:#ffff11">[inline:%s %s]</span>' % (url, text)

    def attachment_link(self, url, text, **kw):
        _ = self.request.getText
        pagename = self.page.page_name
        target = AttachFile.getAttachUrl(pagename, url, self.request)
        return (self.url(1, target, title="attachment:%s" % wikiutil.quoteWikinameURL(url)) +
                self.text(text) +
                self.url(0))

    def attachment_image(self, url, **kw):
        _ = self.request.getText
        pagename = self.page.page_name
        return self.image(
            title="attachment:%s" % wikiutil.quoteWikinameURL(url),
            src=AttachFile.getAttachUrl(pagename, url, self.request, addts=1))

    def attachment_drawing(self, url, text, **kw):
        _ = self.request.getText
        pagename = self.page.page_name
        image = url + u'.png'
        fname = wikiutil.taintfilename(image)
        fpath = AttachFile.getFilename(self.request, pagename, fname)
        return self.image(
            title="drawing:%s" % wikiutil.quoteWikinameURL(url),
            src=AttachFile.getAttachUrl(pagename, image, self.request, addts=1))

    def nowikiword(self, text):
        return '<span style="background-color:#ffff11">!</span>' + self.text(text)

    # Dynamic stuff / Plugins ############################################

    def macro(self, macro_obj, name, args):
        if args is not None:
            result = "[[%s(%s)]]" % (name, args)
        else:
            result = "[[%s]]" % name
        return '<span style="background-color:#ffff11">%s</span>' % result

    def parser(self, parser_name, lines):
        """ parser_name MUST be valid!
        """
        result = [self.preformatted(1)]
        for line in lines:
            result.append(self.text(line))
            result.append(self.linebreak(preformatted=1))
        result.append(self.preformatted(0))

        return "".join(result)

    # Other ##############################################################

    style2attribute = {
        'width': 'width',
        'height': 'height',
        'background': 'bgcolor',
        'background-color': 'bgcolor',
        #if this is used as table style="text-align: right", it doesn't work
        #if it is transformed to align="right":
        #'text-align': 'align',
        #'vertical-align': 'valign'
        }

    def _style_to_attributes(self, attrs):
        if not attrs.has_key('style'):
            return attrs
        unknown = []
        for entry in attrs['style'].split(';'):
            try:
                key, value = entry.split(':')
            except ValueError:
                unknown.append(entry)
                continue
            key, value = key.strip(), value.strip()
            if self.style2attribute.has_key(key):
                attrs[self.style2attribute[key]] = value
            else:
                unknown.append("%s:%s" % (key, value))
        if unknown:
            attrs['style'] = ';'.join(unknown)
        else:
            del attrs['style']
        return attrs

    def _checkTableAttr(self, attrs, prefix):
        #self.request.log(repr(attrs))
        attrs = text_html.Formatter._checkTableAttr(self, attrs, prefix)
        #self.request.log(repr(attrs))
        attrs = self._style_to_attributes(attrs)
        #self.request.log(repr(attrs))
        return attrs

    _allowed_table_attrs = {
        'table': ['class', 'id', 'style', 'bgcolor', 'width', 'height', ],
        'row': ['class', 'id', 'style', 'bgcolor', 'width', 'height', ],
        '': ['colspan', 'rowspan', 'class', 'id', 'style', 'bgcolor', 'width', ],
    }

    def table(self, on, attrs=None, **kw):
        """ Create table

        @param on: start table
        @param attrs: table attributes
        @rtype: string
        @return start or end tag of a table
        """
        result = []
        if on:
            # Open table
            if not attrs:
                attrs = {}
            else:
                #result.append(self.rawHTML("<!-- ATTRS1: %s -->" % repr(attrs)))
                attrs = self._checkTableAttr(attrs, 'table')
                #result.append(self.rawHTML("<!-- ATTRS2: %s -->" % repr(attrs)))
            result.append(self._open('table', newline=1, attr=attrs,
                                     allowed_attrs=self._allowed_table_attrs['table'],
                                     **kw))
        else:
            # Close table then div
            result.append(self._close('table'))

        return ''.join(result)

    def comment(self, text, **kw):
        text = text.rstrip() # workaround for growing amount of blanks at EOL
        return self.preformatted(1, css_class='comment') + text + self.preformatted(0)

    def strong(self, on, **kw):
        tag = 'b'
        if on:
            return self._open(tag, allowed_attrs=[], **kw)
        return self._close(tag)

    def emphasis(self, on, **kw):
        tag = 'i'
        if on:
            return self._open(tag, allowed_attrs=[], **kw)
        return self._close(tag)

    def underline(self, on, **kw):
        tag = 'u'
        if on:
            return self._open(tag, allowed_attrs=[], **kw)
        return self._close(tag)

    def line_anchordef(self, lineno):
        return '' # not needed for gui editor feeding

    def line_anchorlink(self, on, lineno=0):
        return '' # not needed for gui editor feeding

