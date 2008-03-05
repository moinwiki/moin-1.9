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

    # If the current node is one of the following and we are about the emit
    # text, the text should be wrapped in a paragraph
    wrap_text_in_para = ('listitem', 'glossdef', 'article', 'chapter', 'tip', 'warning', 'note', 'caution', 'important')

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
        elif self.cur.nodeName in self.wrap_text_in_para:
            """
            If we already wrapped one text item in a para, we should add to that para
            and not create a new one. Another question is if we should add a space?
            """
            if self.cur.lastChild is not None and self.cur.lastChild.nodeName == 'para':
                self.cur.lastChild.appendChild(self.doc.createTextNode(srcText))
            else:
                self.paragraph(1)
                self.text(text)
                self.paragraph(0)
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
        """
        If preformatted, it will simply output a linebreak.
        If we are in a paragraph, we will close it, and open another one.
        """
        if preformatted:
            self.text('\\n')
        elif self.cur.nodeName == "para":
            self.paragraph(0)
            self.paragraph(1)
        else:
            self._emitComment("Warning: Probably not emitting right sort of linebreak")
            self.text('\n')
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

        elif name == "FootNote":
            footnote = self.doc.createElement('footnote')
            para = self.doc.createElement('para')
            para.appendChild(self.doc.createTextNode(str(args)))
            footnote.appendChild(para)
            self.cur.appendChild(footnote)

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

    def _convertStylesToDict(self, styles):
        '''Takes the CSS styling information and converts it to a dict'''
        attrs = {}
        for s in styles.split(";"):
            if s.strip(' "') == "":
                continue
            (key, value) = s.split(":", 1)
            key = key.strip(' "')
            value = value.strip(' "')

            if key == 'vertical-align':
                key = 'valign'
            elif key == 'text-align':
                key = 'align'
            elif key == 'background-color':
                key = 'bgcolor'

            attrs[key] = value
        return attrs


### Not supported ###################################################

    def rule(self, size=0, **kw):
        return ""

    def small(self, on, **kw):
        return ""

    def big(self, on, **kw):
        return ""

### Tables ##########################################################

    def table(self, on, attrs=(), **kw):
        if(on):
            self.curtable = Table(self, self.doc, self.cur, attrs)
            self.cur = self.curtable.tableNode
        else:
            self.cur = self.curtable.finalizeTable()
            self.curtable = None
        return ""

    def table_row(self, on, attrs=(), **kw):
        if(on):
            self.cur = self.curtable.addRow(attrs)
        return ""

    def table_cell(self, on, attrs=(), **kw):
        if(on):
            self.cur = self.curtable.addCell(attrs)
        return ""

class Table:
    '''The Table class is used as a helper for collecting information about
    what kind of table we are building. When all relelvant data is gathered
    it calculates the different spans of the cells and columns.
    '''

    def __init__(self, formatter, doc, parent, args):
        self.formatter = formatter
        self.doc = doc

        self.tableNode = self.doc.createElement('informaltable')
        parent.appendChild(self.tableNode)
        self.colWidths = {}
        self.tgroup = self.doc.createElement('tgroup')
        # Bug in yelp, the two lines below don't affect rendering
        #self.tgroup.setAttribute('rowsep', '1')
        #self.tgroup.setAttribute('colsep', '1')
        self.curColumn = 0
        self.maxColumn = 0
        self.row = None
        self.tableNode.appendChild(self.tgroup)

        self.tbody = self.doc.createElement('tbody') # Note: This gets appended in finalizeTable

    def finalizeTable(self):
        """Calculates the final width of the whole table and the width of each
        column. Adds the colspec-elements and applies the colwidth attributes.
        Inserts the tbody element to the tgroup and returns the tables container
        element.
		
        A lot of the information is gathered from the style attributes passed
        to the functions
        """
        self.tgroup.setAttribute('cols', str(self.maxColumn))
        for colnr in range(0, self.maxColumn):
            colspecElem = self.doc.createElement('colspec')
            colspecElem.setAttribute('colname', 'col_%s' % str(colnr))
            if self.colWidths.has_key(str(colnr)) and self.colWidths[str(colnr)] != "1*":
                colspecElem.setAttribute('colwidth', self.colWidths[str(colnr)])
            self.tgroup.appendChild(colspecElem)
        self.tgroup.appendChild(self.tbody)
        return self.tableNode.parentNode

    def addRow(self, args):
        self.curColumn = 0
        self.row = self.doc.createElement('row')
        # Bug in yelp, doesn't affect the outcome.
        #self.row.setAttribute("rowsep", "1") #Rows should have lines between them
        self.tbody.appendChild(self.row)
        return self.row

    def addCell(self, args):
        cell = self.doc.createElement('entry')
        cell.setAttribute('rowsep', '1')
        cell.setAttribute('colsep', '1')

        self.row.appendChild(cell)

        args = self._convertStyleAttributes(args)
        self._handleSimpleCellAttributes(cell, args)
        self._handleColWidth(args)
        self.curColumn += self._handleColSpan(cell, args)

        self.maxColumn = max(self.curColumn, self.maxColumn)

        return cell

    def _handleColWidth(self, args):
        if not args.has_key("width"):
            return
        args["width"] = args["width"].strip('"')
        if not args["width"].endswith("%"):
            self.formatter._emitComment("Width %s not supported" % args["width"])
            return

        self.colWidths[str(self.curColumn)] = args["width"][:-1] + "*"

    def _handleColSpan(self, element, args):
        """Returns the number of colums this entry spans"""
        if not args or not args.has_key('colspan'):
            return 1
        assert(element.nodeName == "entry")
        extracols = int(args['colspan'].strip('"')) - 1
        element.setAttribute('namest', "col_" + str(self.curColumn))
        element.setAttribute('nameend', "col_" + str(self.curColumn + extracols))
        return 1 + extracols

    def _handleSimpleCellAttributes(self, element, args):
        safe_values_for = {'valign': ('top', 'middle', 'bottom'),
                           'align': ('left', 'center', 'right'),
                          }
        if not args:
            return
        assert(element.nodeName == "entry")

        if args.has_key('rowspan'):
            extrarows = int(args['rowspan'].strip('"')) - 1
            element.setAttribute('morerows', str(extrarows))

        if args.has_key('align'):
            value = args['align'].strip('"')
            if value in safe_values_for['align']:
                element.setAttribute('align', value)
            else:
                self.formatter._emitComment("Alignment %s not supported" % value)
                pass

        if args.has_key('valign'):
            value = args['valign'].strip('"')
            if value in safe_values_for['valign']:
                element.setAttribute('valign', value)
            else:
                self.formatter._emitComment("Vertical alignment %s not supported" % value)
                pass

    def _convertStyleAttributes(self, argslist):
        if not argslist.has_key('style'):
            return argslist
        styles = self.formatter._convertStylesToDict(argslist['style'].strip('"'))
        argslist.update(styles)

        return argslist
