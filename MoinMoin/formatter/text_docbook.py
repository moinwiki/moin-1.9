# -*- coding: utf-8 -*-
"""
    MoinMoin - DocBook Formatter

    @copyright: 2005,2008 by Mikko Virkkilä <mvirkkil@cc.hut.fi>
    @copyright: 2005 by MoinMoin:AlexanderSchremmer (small modifications)
    @copyright: 2005 by MoinMoin:Petr Pytelka <pyta@lightcomp.com> (small modifications)

    @license: GNU GPL, see COPYING for details.
"""

import os
from xml.dom import getDOMImplementation
from xml.dom.ext.reader import Sax
from xml.dom.ext import Node

from MoinMoin.formatter import FormatterBase
from MoinMoin import wikiutil
from MoinMoin.error import CompositeError
from MoinMoin.action import AttachFile

class InternalError(CompositeError): pass

try:
    dom = getDOMImplementation("4DOM")
except ImportError:
    raise InternalError("You need to install 4suite to use the DocBook formatter.")


class Formatter(FormatterBase):

    #this list is extended as the page is parsed. Could be optimized by adding them here?
    section_should_break = ['abstract', 'para', 'emphasis']
 
    blacklisted_macros = ('TableOfContents', 'ShowSmileys')

    def __init__(self, request, doctype="article", **kw):
        FormatterBase.__init__(self, request, **kw)
        self.request = request
        
        '''
        If the formatter is used by the Include macro, it will set 
        is_included=True in which case we know we need to call startDocument 
        and endDocument from startContent and endContent respectively, since
        the Include macro will not be calling them, and the formatter doesn't
        work properly unless they are called.
        '''
        if kw.has_key("is_included") and kw["is_included"]:
            self.include_kludge = True
        else:
            self.include_kludge = False

        self.doctype = doctype
        self.curdepth = 0
        self.cur = None

    def startDocument(self, pagename):
        self.doc = dom.createDocument(None, self.doctype, dom.createDocumentType(
            self.doctype, "-//OASIS//DTD DocBook XML V4.4//EN",
            "http://www.docbook.org/xml/4.4/docbookx.dtd"))

        self.title = pagename
        self.root = self.doc.documentElement
        self.curdepth = 0

        #info = self.doc.createElement("articleinfo")
        self._addTitleElement(self.title, targetNode=self.root)
        self.cur = self.root
        return ""

    def startContent(self, content_id="content", **kw):
        if self.include_kludge and not self.cur:
            return self.startDocument("OnlyAnIdiotWouldCreateSuchaPage")
        return ""

    def endContent(self):
        if self.include_kludge:
            return self.endDocument()
        return ""

    def endDocument(self):
        from xml.dom.ext import PrettyPrint, Print
        import StringIO

        f = StringIO.StringIO()
        Print(self.doc, f)
        #PrettyPrint(self.doc, f)
        txt = f.getvalue()
        f.close()

        self.cur = None
        return txt

    def text(self, text, **kw):
        if text == "\\n":
            srcText = "\n"
        else:
            srcText = text
        if self.cur.nodeName == "screen":
            if self.cur.lastChild is not None:
                from xml.dom.ext import Node
                if self.cur.lastChild.nodeType == Node.CDATA_SECTION_NODE:
                    self.cur.lastChild.nodeValue = self.cur.lastChild.nodeValue + srcText
            else:
                self.cur.appendChild(self.doc.createCDATASection(srcText))
        else:
            self.cur.appendChild(self.doc.createTextNode(srcText))
        return ""

    def heading(self, on, depth, **kw):
        while self.cur.nodeName in self.section_should_break:
            self.cur = self.cur.parentNode

        if on:
            # try to go to higher level if needed
            if depth <= self.curdepth:
                # number of levels we want to go higher
                numberOfLevels = self.curdepth - depth + 1
                for dummy in range(numberOfLevels):
                    #find first non section node
                    while (self.cur.nodeName != "section" and self.cur.nodeName != "article"):
                        self.cur = self.cur.parentNode

# I don't understand this code - looks like unnecessary -- maybe it is used to gain some vertical space for large headings?
#                    if len(self.cur.childNodes) < 3:
#                       self._addEmptyNode("para")

                    # check if not top-level
                    if self.cur.nodeName != "article":
                        self.cur = self.cur.parentNode

            section = self.doc.createElement("section")
            self.cur.appendChild(section)
            self.cur = section

            title = self.doc.createElement("title")
            self.cur.appendChild(title)
            self.cur = title
            self.curdepth = depth
        else:
            self.cur = self.cur.parentNode

        return ""

    def paragraph(self, on, **kw):
        FormatterBase.paragraph(self, on)

        # Let's prevent para inside para
        if on and self.cur.nodeName == "para":
            return ""
        return self._handleNode("para", on)

    def linebreak(self, preformatted=1):
        if preformatted:
            self.text('\\n')
        else:
            #this should not happen
            #self.text('CRAP')
            pass
        return ""

    def _handleNode(self, name, on, attributes=()):
        if on:
            node = self.doc.createElement(name)
            self.cur.appendChild(node)
            if len(attributes) > 0:
                for name, value in attributes:
                    node.setAttribute(name, value)
            self.cur = node
        else:
            """
                Because we prevent para inside para, we might get extra "please exit para"
                when we are no longer inside one.

                TODO: Maybe rethink the para in para case
            """
            if name == "para" and self.cur.nodeName != "para":
                return ""

            self.cur = self.cur.parentNode
        return ""

    def _addEmptyNode(self, name, attributes=()):
        node = self.doc.createElement(name)
        self.cur.appendChild(node)
        if len(attributes) > 0:
            for name, value in attributes:
                node.setAttribute(name, value)

    def _getTableCellCount(self, attrs=()):
        cols = 1
        if attrs and attrs.has_key('colspan'):
            s1 = attrs['colspan']
            s1 = str(s1).replace('"', '')
            cols = int(s1)
        return cols

    def _addTableCellDefinition(self, attrs=()):
        # Check number of columns
        cols = self._getTableCellCount(attrs)
        # Find node tgroup
        actNode = self.cur
        numberExistingColumns = 0
        while actNode and actNode.nodeName != 'tgroup':
            actNode = actNode.parentNode
        # Number of existing columns
        nodeBefore = self.cur
        if actNode:
            nodeBefore = actNode.firstChild
        while nodeBefore and nodeBefore.nodeName != 'tbody':
            nodeBefore = nodeBefore.nextSibling
            numberExistingColumns += 1

        while cols >= 1:
            # Create new node
            numberExistingColumns += 1
            nnode = self.doc.createElement("colspec")
            nnode.setAttribute('colname', 'xxx' + str(numberExistingColumns))
            # Add node
            if actNode:
                actNode.insertBefore(nnode, nodeBefore)
            else:
                self.cur.insertBefore(nnode, nodeBefore)
            cols -= 1
        # Set new number of columns for tgroup
        self.cur.parentNode.parentNode.parentNode.setAttribute('cols', str(numberExistingColumns))
        return ""


### Inline ##########################################################

    def _handleFormatting(self, name, on, attributes=()):
        # We add all the elements we create to the list of elements that should not contain a section
        if name not in self.section_should_break:
            self.section_should_break.append(name)

        return self._handleNode(name, on, attributes)

    def strong(self, on, **kw):
        return self._handleFormatting("emphasis", on, (('role', 'strong'), ))

    def emphasis(self, on, **kw):
        return self._handleFormatting("emphasis", on)

    def underline(self, on, **kw):
        return self._handleFormatting("emphasis", on, (('role', 'underline'), ))

    def highlight(self, on, **kw):
        return self._handleFormatting("emphasis", on, (('role', 'highlight'), ))

    def sup(self, on, **kw):
        return self._handleFormatting("superscript", on)

    def sub(self, on, **kw):
        return self._handleFormatting("subscript", on)

    def strike(self, on, **kw):
        # does not yield <strike> using the HTML XSLT files here ...
        # but seems to be correct
        return self._handleFormatting("emphasis", on,
                                      (('role', 'strikethrough'), ))

    def code(self, on, **kw):
        return self._handleFormatting("code", on)

    def preformatted(self, on, **kw):
        return self._handleFormatting("screen", on)


### Lists ###########################################################

    def number_list(self, on, type=None, start=None, **kw):
        docbook_ol_types = {'1': "arabic",
                            'a': "loweralpha",
                            'A': "upperalpha",
                            'i': "lowerroman",
                            'I': "upperroman"}

        if type and docbook_ol_types.has_key(type):
            attrs = [("numeration", docbook_ol_types[type])]
        else:
            attrs = []

        return self._handleNode('orderedlist', on, attrs)

    def bullet_list(self, on, **kw):
        return self._handleNode("itemizedlist", on)

    def definition_list(self, on, **kw):
        return self._handleNode("glosslist", on)

    def definition_term(self, on, compact=0, **kw):
       # When on is false, we back out just on level. This is
       # ok because we know definition_desc gets called, and we
       # back out two levels there.
        if on:
            entry = self.doc.createElement('glossentry')
            term = self.doc.createElement('glossterm')
            entry.appendChild(term)
            self.cur.appendChild(entry)
            self.cur = term
        else:
            self.cur = self.cur.parentNode
        return ""

    def definition_desc(self, on, **kw):
        # We backout two levels when 'on' is false, to leave the glossentry stuff
        if on:
            return self._handleNode("glossdef", on)
        else:
            self.cur = self.cur.parentNode.parentNode
            return ""

    def listitem(self, on, **kw):
        if on:
            node = self.doc.createElement("listitem")
            self.cur.appendChild(node)
            self.cur = node
        else:
            self.cur = self.cur.parentNode
        return ""


### Links ###########################################################

    # FIXME: This is quite crappy
    def pagelink(self, on, pagename='', page=None, **kw):
        FormatterBase.pagelink(self, on, pagename, page, **kw)

        return self.interwikilink(on, 'Self', pagename)

    # FIXME: This is even more crappy
    def interwikilink(self, on, interwiki='', pagename='', **kw):
        if not on:
            return self.url(on, kw)

        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_interwiki(self.request, interwiki, pagename)
        wikiurl = wikiutil.mapURL(self.request, wikiurl)
        href = wikiutil.join_wiki(wikiurl, wikitail)

        return self.url(on, href)

    def url(self, on, url=None, css=None, **kw):
        return self._handleNode("ulink", on, (('url', url), ))

    def anchordef(self, name):
        self._handleNode("anchor", True, (('id', name), ))
        self._handleNode("ulink", False)
        return ""

    def anchorlink(self, on, name='', **kw):
        id = kw.get('id', None)
        attrs = []
        if name != '':
            attrs.append(('endterm', name))
        if id is not None:
            attrs.append(('linkend', id))
        elif name != '':
            attrs.append(('linkend', name))

        return self._handleNode("link", on, attrs)

### Attachments ######################################################

    def attachment_link(self, on, url=None, **kw):
        assert on in (0, 1, False, True) # make sure we get called the new way, not like the 1.5 api was
        # we do not output a "upload link" when outputting docbook
        if on:
            pagename, filename = AttachFile.absoluteName(url, self.page.page_name)
            fname = wikiutil.taintfilename(filename)
            target = AttachFile.getAttachUrl(pagename, filename, self.request)
            return self.url(1, target, title="attachment:%s" % url)
        else:
            return self.url(0)

    def attachment_image(self, url, **kw):
        _ = self.request.getText
        pagename, filename = AttachFile.absoluteName(url, self.page.page_name)
        fname = wikiutil.taintfilename(filename)
        fpath = AttachFile.getFilename(self.request, pagename, fname)
        if not os.path.exists(fpath):
            return self.text("[attachment:%s]" % url)
        else:
            src = AttachFile.getAttachUrl(pagename, filename, self.request, addts=1)
            return self.image(src=src, title="attachment:%s" % url)

    def attachment_drawing(self, url, text, **kw):
        _ = self.request.getText
        pagename, filename = AttachFile.absoluteName(url, self.page.page_name)
        fname = wikiutil.taintfilename(filename)
        drawing = fname
        fname = fname + ".png"
        filename = filename + ".png"
        fpath = AttachFile.getFilename(self.request, pagename, fname)
        if not os.path.exists(fpath):
            return self.text("[drawing:%s]" % url)
        else:
            src = AttachFile.getAttachUrl(pagename, filename, self.request, addts=1)
            return self.image(alt=drawing, src=src, html_class="drawing")

### Images and Smileys ##############################################

    def image(self, src=None, **kw):
        if src:
            kw['src'] = src
        media = self.doc.createElement('inlinemediaobject')

        imagewrap = self.doc.createElement('imageobject')
        media.appendChild(imagewrap)

        image = self.doc.createElement('imagedata')
        if kw.has_key('src'):
            image.setAttribute('fileref', kw['src'])
        if kw.has_key('width'):
            image.setAttribute('width', str(kw['width']))
        if kw.has_key('height'):
            image.setAttribute('depth', str(kw['height']))
        imagewrap.appendChild(image)

        title = ''
        for a in ('title', 'html_title', 'alt', 'html_alt'):
            if kw.has_key(a):
                title = kw[a]
                break
        if title:
            txtcontainer = self.doc.createElement('textobject')
            media.appendChild(txtcontainer)
            txtphrase = self.doc.createElement('phrase')
            txtphrase.appendChild(self.doc.createTextNode(title))
            txtcontainer.appendChild(txtphrase)

        self.cur.appendChild(media)
        return ""

    def transclusion(self, on, **kw):
        # TODO, see text_html formatter
        return ""

    def transclusion_param(self, **kw):
        # TODO, see text_html formatter
        return ""

    def smiley(self, text):
        return self.request.theme.make_icon(text)

    def icon(self, type):
        return '' # self.request.theme.make_icon(type)

### Tables ##########################################################

    #FIXME: We should copy code from text_html.py for attr handling

    def table(self, on, attrs=None, **kw):
        sanitized_attrs = []
        if attrs and attrs.has_key('id'):
            sanitized_attrs[id] = attrs['id']

        self._handleNode("table", on, sanitized_attrs)
        if on:
            self._addEmptyNode("caption") #dtd for table requires caption
        self._handleNode("tgroup", on)
        self._handleNode("tbody", on)
        return ""

    def table_row(self, on, attrs=None, **kw):
        self.table_current_row_cells = 0
        sanitized_attrs = []
        if attrs and attrs.has_key('id'):
            sanitized_attrs[id] = attrs['id']
        return self._handleNode("row", on, sanitized_attrs)

    def table_cell(self, on, attrs=None, **kw):
        # Finish row definition
        sanitized_attrs = []
        if attrs and attrs.has_key('id'):
            sanitized_attrs[id] = attrs['id']
        # Get number of newly added columns
        startCount = self.table_current_row_cells
        addedCellsCount = self._getTableCellCount(attrs)
        self.table_current_row_cells += addedCellsCount
        ret = self._handleNode("entry", on, sanitized_attrs)
        if self.cur.parentNode == self.cur.parentNode.parentNode.firstChild:
            self._addTableCellDefinition(attrs)
        # Set cell join if any
        if addedCellsCount > 1:
            startString = "xxx" + str(startCount)
            stopString = "xxx" + str(startCount + addedCellsCount - 1)
            self.cur.setAttribute("namest", startString)
            self.cur.setAttribute("nameend", stopString)
        return ret

### Code ############################################################

    def code_area(self, on, code_id, code_type='code', show=0, start=-1, step=-1):
        show = show and 'numbered' or 'unnumbered'
        if start < 1:
            start = 1

        attrs = (('id', code_id),
                ('linenumbering', show),
                ('startinglinenumber', str(start)),
                ('language', code_type),
                ('format', 'linespecific'),
                )
        return self._handleFormatting("screen", on, attrs)

    def code_line(self, on):
        return '' # No clue why something should be done here

    def code_token(self, on, tok_type):
        toks_map = {'ID': 'methodname',
                    'Operator': '',
                    'Char': '',
                    'Comment': 'lineannotation',
                    'Number': '',
                    'String': 'phrase',
                    'SPChar': '',
                    'ResWord': 'token',
                    'ConsWord': 'symbol',
                    'Error': 'errortext',
                    'ResWord2': '',
                    'Special': '',
                    'Preprc': '',
                    'Text': ''}
        if toks_map.has_key(tok_type) and toks_map[tok_type] != '':
            return self._handleFormatting(toks_map[tok_type], on)
        else:
            return ""

    def macro(self, macro_obj, name, args, markup=None):
        if name in self.blacklisted_macros:
            self._emitComment("The macro %s doesn't work with the DocBook formatter." % name)
        elif name == "Include":
            text = FormatterBase.macro(self, macro_obj, name, args)
            if text.strip():
                self._copyExternalNodes(Sax.FromXml(text).documentElement.childNodes, exclude=("title",))
        else:
            text = FormatterBase.macro(self, macro_obj, name, args)
            if text:
                from xml.parsers.expat import ExpatError
                try:
                    self._copyExternalNodes(Sax.FromXml(text).documentElement.childNodes, exclude=excludes)
                except ExpatError:
                    self._emitComment("The macro %s caused an error and should be blacklisted. It returned the data '%s' which caused the docbook-formatter to choke. Please file a bug." % (name, text))

        return u""

    def _copyExternalNodes(self, nodes, deep=1, target=None, exclude=()):
        if not target:
            target = self.cur

        for node in nodes:
            if node.nodeName in exclude:
                pass
            elif target.nodeName == "para" and node.nodeName == "para":
                self._copyExternalNodes(node.childNodes, target=target)
                self.cur = target.parentNode
            else:
                target.appendChild(self.doc.importNode(node, deep))

    def _emitComment(self, text):
        text = text.replace("--", "- -") # There cannot be "--" in XML comment
        self.cur.appendChild(self.doc.createComment(text))

    def _addTitleElement(self, titleTxt, targetNode=None):
        if not targetNode:
            targetNode = self.cur
        title = self.doc.createElement("title")
        title.appendChild(self.doc.createTextNode(titleTxt))
        targetNode.appendChild(title)


### Not supported ###################################################

    def rule(self, size=0, **kw):
        return ""

    def small(self, on, **kw):
        return ""

    def big(self, on, **kw):
        return ""

