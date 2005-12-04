# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "text/html+css" Formatter

    @copyright: (c) Bastian Blank, Florian Festi, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.formatter import text_html
from MoinMoin.formatter.base import FormatterBase
from MoinMoin import wikiutil, config
from MoinMoin.Page import Page
from MoinMoin.action import AttachFile

class Formatter(text_html.Formatter):
    """
        Send HTML data.
    """

    # Block elements ####################################################

    def heading(self, on, depth, id = None, **kw):
        # remember depth of first heading, and adapt counting depth accordingly
        if not self._base_depth:
            self._base_depth = depth

        count_depth = max(depth - (self._base_depth - 1), 1)
        heading_depth = depth + 1

        # closing tag, with empty line after, to make source more readable
        if not on:
            return self.close('h%d' % heading_depth)
        else:
            return self.open('h%d' % heading_depth)

    # Links ##############################################################

    def pagelink(self, on, pagename='', page=None, **kw):
        """ Link to a page.

            formatter.text_python will use an optimized call with a page!=None
            parameter. DO NOT USE THIS YOURSELF OR IT WILL BREAK.

            See wikiutil.link_tag() for possible keyword parameters.
        """
        apply(FormatterBase.pagelink, (self, on, pagename, page), kw)
        if page is None:
            page = Page(self.request, pagename, formatter=self);
        return page.link_to(self.request, on=on, **kw)

    def interwikilink(self, on, interwiki='', pagename='', **kw):
        """
        @keyword title: override using the interwiki wikiname as title
        """
        if not on:
            return '</a>'
        html_class = 'badinterwiki' # we use badinterwiki in any case to simplify reverse conversion
        href = wikiutil.quoteWikinameURL(pagename)
        title = kw.get('title', interwiki)
        return self.url(1, href, title=title, unescaped=0, css=html_class)
        # unescaped=1 was changed to 0 to make interwiki links with pages with umlauts (or other non-ascii) work

    '''
    def attachment_link(self, url, text, **kw):
        if url==text:
            return "attachment:%s" % url
        else:
            return "[attachment:%s %s]" % (url, text)
    
    def attachment_image(self, url, **kw):
        return "attachment:%s" % url
    
    def attachment_drawing(self, url, text, **kw):
        if url==text:
            return "drawing:%s" % url
        else:
            return "[drawing:%s %s]" % (url, text)
'''
    
    def attachment_inlined(self, url, text, **kw):
        if url==text:
            return '<span style="background-color:#ffff11">inline:%s</span>' % url
        else:
            return '<span style="background-color:#ffff11">[inline:%s %s]</span>' % (url, text)

    def attachment_link(self, url, text, **kw):
        _ = self.request.getText
        pagename = self.page.page_name
        target = AttachFile.getAttachUrl(pagename, url, self.request)
        return (self.url(
            1, target,
            title="attachment:%s" % wikiutil.quoteWikinameURL(url)) +
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
        # call the macro
        if args is not None:
            result =  "[[%s(%s)]]" % (name, args)    
        else:
            result = "[[%s]]" % name
        return '<span style="background-color:#ffff11">%s</span>' % result

    def processor(self, processor_name, lines, is_parser = 0):
        """ processor_name MUST be valid!
            writes out the result instead of returning it!
        """
        result = [self.preformatted(1)]
        for line in lines:
            result.append(self.text(line))
            result.append(self.linebreak(preformatted=1))
        result.append(self.preformatted(0))

        return "".join(result)


    # Lists ##############################################################

    # Change nesting: sub lists are no longer within the <li> tags
    
    def number_list(self, on, type=None, start=None):
        li = ""
        if self._in_li: # close <li>
            li = self.listitem(False)
        return li + text_html.Formatter.number_list(self, on, type, start)

    def bullet_list(self, on):
        li = ""
        if self._in_li: # close <li>
            li = self.listitem(False)
        return li + text_html.Formatter.bullet_list(self, on)

    def listitem(self, on, **kw):
        # only if not already closed
        if on or self._in_li:
            return text_html.Formatter.listitem(self, on, **kw)
        else:
            return ""

    # Other ##############################################################

    style2attribute = {
        'width': 'width',
        'height': 'height',
        'background' : 'bgcolor',
        'background-color' : 'bgcolor',
        #if this is used as table style="text-align: right", it doesn't work
        #if it is transformed to align="right":
        #'text-align' : 'align',
        #'vertical-align' : 'valign'
        }

    def _style_to_attributes(self, attrs):
        if not attrs.has_key('style'):
            return
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
        attrs = text_html.Formatter._checkTableAttr(self, attrs, prefix)
        return self._style_to_attributes(attrs)

    def table(self, on, attrs=None):
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
            result.append(self.open('table', newline=1, attr=attrs))
        else:
            # Close table then div
            result.append(self.close('table'))

        return ''.join(result)    

    def comment(self, text):
        text = text.rstrip() # workaround for growing amount of blanks at EOL
        return self.preformatted(1, attr={'class': 'comment'}) + text + self.preformatted(0)

    def underline(self, on):
        tag = 'u'
        if on:
            return self.open(tag)
        return self.close(tag)
                    
    def strong(self, on):
        tag = 'b'
        if on:
            return self.open(tag)
        return self.close(tag)

    def emphasis(self, on):
        tag = 'i'
        if on:
            return self.open(tag)
        return self.close(tag)

    def code(self, on, css=None):
        tag = 'tt'
        # Maybe we don't need this, because we have tt will be in inlineStack.
        self._in_code = on
        if css:
            attrs = {"css":css}
        else:
            attrs = None

        if on:
            return self.open(tag, attr=attrs)
        return self.close(tag)

    def line_anchordef(self, lineno):
        return '' # not needed for gui editor feeding
        
    def line_anchorlink(self, on, lineno=0):
        return '' # not needed for gui editor feeding

