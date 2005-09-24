"""
    MoinMoin - convert from html to wiki markup

    @copyright: (c) Bastian Blank, Florian Festi, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import xml.dom.minidom
from xml.dom import Node
from MoinMoin import config
from MoinMoin import wikiutil
import MoinMoin.error
import re, urllib

# Portions (C) International Organization for Standardization 1986
# Permission to copy in any form is granted for use with
# conforming SGML systems and applications as defined in
# ISO 8879, provided this notice is included in all copies.
dtd = ur'''
<!DOCTYPE html [
<!ENTITY nbsp   "&#32;">  <!-- no-break space = non-breaking space, U+00A0, convert to U+0020 -->
<!ENTITY iexcl  "&#161;"> <!-- inverted exclamation mark, U+00A1 ISOnum -->
<!ENTITY cent   "&#162;"> <!-- cent sign, U+00A2 ISOnum -->
<!ENTITY pound  "&#163;"> <!-- pound sign, U+00A3 ISOnum -->
<!ENTITY curren "&#164;"> <!-- currency sign, U+00A4 ISOnum -->
<!ENTITY yen    "&#165;"> <!-- yen sign = yuan sign, U+00A5 ISOnum -->
<!ENTITY brvbar "&#166;"> <!-- broken bar = broken vertical bar, U+00A6 ISOnum -->
<!ENTITY sect   "&#167;"> <!-- section sign, U+00A7 ISOnum -->
<!ENTITY uml    "&#168;"> <!-- diaeresis = spacing diaeresis, U+00A8 ISOdia -->
<!ENTITY copy   "&#169;"> <!-- copyright sign, U+00A9 ISOnum -->
<!ENTITY ordf   "&#170;"> <!-- feminine ordinal indicator, U+00AA ISOnum -->
<!ENTITY laquo  "&#171;"> <!-- left-pointing double angle quotation mark = left pointing guillemet, U+00AB ISOnum -->
<!ENTITY not    "&#172;"> <!-- not sign = angled dash, U+00AC ISOnum -->
<!ENTITY shy    "&#173;"> <!-- soft hyphen = discretionary hyphen, U+00AD ISOnum -->
<!ENTITY reg    "&#174;"> <!-- registered sign = registered trade mark sign, U+00AE ISOnum -->
<!ENTITY macr   "&#175;"> <!-- macron = spacing macron = overline = APL overbar, U+00AF ISOdia -->
<!ENTITY deg    "&#176;"> <!-- degree sign, U+00B0 ISOnum -->
<!ENTITY plusmn "&#177;"> <!-- plus-minus sign = plus-or-minus sign, U+00B1 ISOnum -->
<!ENTITY sup2   "&#178;"> <!-- superscript two = superscript digit two = squared, U+00B2 ISOnum -->
<!ENTITY sup3   "&#179;"> <!-- superscript three = superscript digit three = cubed, U+00B3 ISOnum -->
<!ENTITY acute  "&#180;"> <!-- acute accent = spacing acute, U+00B4 ISOdia -->
<!ENTITY micro  "&#181;"> <!-- micro sign, U+00B5 ISOnum -->
<!ENTITY para   "&#182;"> <!-- pilcrow sign = paragraph sign, U+00B6 ISOnum -->
<!ENTITY middot "&#183;"> <!-- middle dot = Georgian comma = Greek middle dot, U+00B7 ISOnum -->
<!ENTITY cedil  "&#184;"> <!-- cedilla = spacing cedilla, U+00B8 ISOdia -->
<!ENTITY sup1   "&#185;"> <!-- superscript one = superscript digit one, U+00B9 ISOnum -->
<!ENTITY ordm   "&#186;"> <!-- masculine ordinal indicator, U+00BA ISOnum -->
<!ENTITY raquo  "&#187;"> <!-- right-pointing double angle quotation mark = right pointing guillemet, U+00BB ISOnum -->
<!ENTITY frac14 "&#188;"> <!-- vulgar fraction one quarter = fraction one quarter, U+00BC ISOnum -->
<!ENTITY frac12 "&#189;"> <!-- vulgar fraction one half = fraction one half, U+00BD ISOnum -->
<!ENTITY frac34 "&#190;"> <!-- vulgar fraction three quarters = fraction three quarters, U+00BE ISOnum -->
<!ENTITY iquest "&#191;"> <!-- inverted question mark = turned question mark, U+00BF ISOnum -->
<!ENTITY Agrave "&#192;"> <!-- latin capital letter A with grave = latin capital letter A grave, U+00C0 ISOlat1 -->
<!ENTITY Aacute "&#193;"> <!-- latin capital letter A with acute, U+00C1 ISOlat1 -->
<!ENTITY Acirc  "&#194;"> <!-- latin capital letter A with circumflex, U+00C2 ISOlat1 -->
<!ENTITY Atilde "&#195;"> <!-- latin capital letter A with tilde, U+00C3 ISOlat1 -->
<!ENTITY Auml   "&#196;"> <!-- latin capital letter A with diaeresis, U+00C4 ISOlat1 -->
<!ENTITY Aring  "&#197;"> <!-- latin capital letter A with ring above = latin capital letter A ring, U+00C5 ISOlat1 -->
<!ENTITY AElig  "&#198;"> <!-- latin capital letter AE = latin capital ligature AE, U+00C6 ISOlat1 -->
<!ENTITY Ccedil "&#199;"> <!-- latin capital letter C with cedilla, U+00C7 ISOlat1 -->
<!ENTITY Egrave "&#200;"> <!-- latin capital letter E with grave, U+00C8 ISOlat1 -->
<!ENTITY Eacute "&#201;"> <!-- latin capital letter E with acute, U+00C9 ISOlat1 -->
<!ENTITY Ecirc  "&#202;"> <!-- latin capital letter E with circumflex, U+00CA ISOlat1 -->
<!ENTITY Euml   "&#203;"> <!-- latin capital letter E with diaeresis, U+00CB ISOlat1 -->
<!ENTITY Igrave "&#204;"> <!-- latin capital letter I with grave, U+00CC ISOlat1 -->
<!ENTITY Iacute "&#205;"> <!-- latin capital letter I with acute, U+00CD ISOlat1 -->
<!ENTITY Icirc  "&#206;"> <!-- latin capital letter I with circumflex, U+00CE ISOlat1 -->
<!ENTITY Iuml   "&#207;"> <!-- latin capital letter I with diaeresis, U+00CF ISOlat1 -->
<!ENTITY ETH    "&#208;"> <!-- latin capital letter ETH, U+00D0 ISOlat1 -->
<!ENTITY Ntilde "&#209;"> <!-- latin capital letter N with tilde, U+00D1 ISOlat1 -->
<!ENTITY Ograve "&#210;"> <!-- latin capital letter O with grave, U+00D2 ISOlat1 -->
<!ENTITY Oacute "&#211;"> <!-- latin capital letter O with acute, U+00D3 ISOlat1 -->
<!ENTITY Ocirc  "&#212;"> <!-- latin capital letter O with circumflex, U+00D4 ISOlat1 -->
<!ENTITY Otilde "&#213;"> <!-- latin capital letter O with tilde, U+00D5 ISOlat1 -->
<!ENTITY Ouml   "&#214;"> <!-- latin capital letter O with diaeresis, U+00D6 ISOlat1 -->
<!ENTITY times  "&#215;"> <!-- multiplication sign, U+00D7 ISOnum -->
<!ENTITY Oslash "&#216;"> <!-- latin capital letter O with stroke = latin capital letter O slash, U+00D8 ISOlat1 -->
<!ENTITY Ugrave "&#217;"> <!-- latin capital letter U with grave, U+00D9 ISOlat1 -->
<!ENTITY Uacute "&#218;"> <!-- latin capital letter U with acute, U+00DA ISOlat1 -->
<!ENTITY Ucirc  "&#219;"> <!-- latin capital letter U with circumflex, U+00DB ISOlat1 -->
<!ENTITY Uuml   "&#220;"> <!-- latin capital letter U with diaeresis, U+00DC ISOlat1 -->
<!ENTITY Yacute "&#221;"> <!-- latin capital letter Y with acute, U+00DD ISOlat1 -->
<!ENTITY THORN  "&#222;"> <!-- latin capital letter THORN, U+00DE ISOlat1 -->
<!ENTITY szlig  "&#223;"> <!-- latin small letter sharp s = ess-zed, U+00DF ISOlat1 -->
<!ENTITY agrave "&#224;"> <!-- latin small letter a with grave = latin small letter a grave, U+00E0 ISOlat1 -->
<!ENTITY aacute "&#225;"> <!-- latin small letter a with acute, U+00E1 ISOlat1 -->
<!ENTITY acirc  "&#226;"> <!-- latin small letter a with circumflex, U+00E2 ISOlat1 -->
<!ENTITY atilde "&#227;"> <!-- latin small letter a with tilde, U+00E3 ISOlat1 -->
<!ENTITY auml   "&#228;"> <!-- latin small letter a with diaeresis, U+00E4 ISOlat1 -->
<!ENTITY aring  "&#229;"> <!-- latin small letter a with ring above = latin small letter a ring, U+00E5 ISOlat1 -->
<!ENTITY aelig  "&#230;"> <!-- latin small letter ae = latin small ligature ae, U+00E6 ISOlat1 -->
<!ENTITY ccedil "&#231;"> <!-- latin small letter c with cedilla, U+00E7 ISOlat1 -->
<!ENTITY egrave "&#232;"> <!-- latin small letter e with grave, U+00E8 ISOlat1 -->
<!ENTITY eacute "&#233;"> <!-- latin small letter e with acute, U+00E9 ISOlat1 -->
<!ENTITY ecirc  "&#234;"> <!-- latin small letter e with circumflex, U+00EA ISOlat1 -->
<!ENTITY euml   "&#235;"> <!-- latin small letter e with diaeresis, U+00EB ISOlat1 -->
<!ENTITY igrave "&#236;"> <!-- latin small letter i with grave, U+00EC ISOlat1 -->
<!ENTITY iacute "&#237;"> <!-- latin small letter i with acute, U+00ED ISOlat1 -->
<!ENTITY icirc  "&#238;"> <!-- latin small letter i with circumflex, U+00EE ISOlat1 -->
<!ENTITY iuml   "&#239;"> <!-- latin small letter i with diaeresis, U+00EF ISOlat1 -->
<!ENTITY eth    "&#240;"> <!-- latin small letter eth, U+00F0 ISOlat1 -->
<!ENTITY ntilde "&#241;"> <!-- latin small letter n with tilde, U+00F1 ISOlat1 -->
<!ENTITY ograve "&#242;"> <!-- latin small letter o with grave, U+00F2 ISOlat1 -->
<!ENTITY oacute "&#243;"> <!-- latin small letter o with acute, U+00F3 ISOlat1 -->
<!ENTITY ocirc  "&#244;"> <!-- latin small letter o with circumflex, U+00F4 ISOlat1 -->
<!ENTITY otilde "&#245;"> <!-- latin small letter o with tilde, U+00F5 ISOlat1 -->
<!ENTITY ouml   "&#246;"> <!-- latin small letter o with diaeresis, U+00F6 ISOlat1 -->
<!ENTITY divide "&#247;"> <!-- division sign, U+00F7 ISOnum -->
<!ENTITY oslash "&#248;"> <!-- latin small letter o with stroke, = latin small letter o slash, U+00F8 ISOlat1 -->
<!ENTITY ugrave "&#249;"> <!-- latin small letter u with grave, U+00F9 ISOlat1 -->
<!ENTITY uacute "&#250;"> <!-- latin small letter u with acute, U+00FA ISOlat1 -->
<!ENTITY ucirc  "&#251;"> <!-- latin small letter u with circumflex, U+00FB ISOlat1 -->
<!ENTITY uuml   "&#252;"> <!-- latin small letter u with diaeresis, U+00FC ISOlat1 -->
<!ENTITY yacute "&#253;"> <!-- latin small letter y with acute, U+00FD ISOlat1 -->
<!ENTITY thorn  "&#254;"> <!-- latin small letter thorn, U+00FE ISOlat1 -->
<!ENTITY yuml   "&#255;"> <!-- latin small letter y with diaeresis, U+00FF ISOlat1 -->
]>
'''

class visitor(object):
    def do(self, tree):
        self.visit_node_list(tree.childNodes)

    def visit_node_list(self, node):
        for i in node:
            self.visit(i)

    def visit(self, node):
        nodeType = node.nodeType
        if node.nodeType == Node.ELEMENT_NODE:
            return self.visit_element(node)
        elif node.nodeType == Node.ATTRIBUTE_NODE:
            return self.visit_attribute(node)
        elif node.nodeType == Node.TEXT_NODE:
            return self.visit_text(node)
        elif node.nodeType == Node.CDATA_SECTION_NODE:
            return self.visit_cdata_section(node)

    def visit_element(self, node):
        if len(node.childNodes):
            self.visit_node_list(node.childNodes)

    def visit_attribute(self, node):
        pass
	
    def visit_text(self, node):
        pass

    def visit_cdata_section(self, node):
        pass


class strip_break(visitor):
    pass


class strip_whitespace(visitor):
    def do(self, tree):
        self.visit_node_list(tree.childNodes)

    def visit_element(self, node):
        if node.localName == 'p':
            # XXX: our formatter adds a whitespace at the end of each paragraph
            if node.hasChildNodes() and node.childNodes[-1].nodeType == Node.TEXT_NODE:
                data = node.childNodes[-1].data.rstrip('\n ')
                # Remove it if empty
                if data == '':
                    node.removeChild(node.childNodes[-1])
                else:
                    node.childNodes[-1].data = data
            # Remove empty paragraphs
            if not node.hasChildNodes():
                node.parentNode.removeChild(node)

        if node.hasChildNodes():
            self.visit_node_list(node.childNodes)


class convert_tree(visitor):
    white_space = object()
    new_line = object()
        
    def __init__(self, request, pagename):
        self.request = request
        self.pagename = pagename
    
    def do(self, tree):
        self.depth = 0
        self.text = []
        self.process_page(tree.documentElement)
        self.check_whitespace()
        return ''.join(self.text)

    def check_whitespace(self):
        i = 0
        text = self.text
        while i < len(text):
            if text[i] is self.white_space:
                if i == 0 or i == len(text)-1:
                    text[0:0] = [" "] # del?
                    i += 1
                elif (text[i-1][-1] in (" ", "\n",) or
                      text[i+1] is self.white_space or
                      text[i+1] is self.new_line):
                    del text[i]
                elif text[i+1][0] in (" ", "\n",):
                    del text[i]
                else:
                    text[i] = " "
                    i += 1
            elif text[i] is self.new_line:
                if i == 0:
                    del text[i]
                elif i == len(text) - 1:
                    text[i] = "\n"
                    i += 1
                elif text[i-1][-1] == "\n" or (
                      isinstance(text[i+1], str) and text[i+1][0] == "\n"):
                    del text[i]
                else:
                    text[i] = "\n"
                    i += 1
            else:
                i += 1

    def visit_element(self, node):
        name = node.localName.lower()

        func = getattr(self, "process_" + name,  None)
        if func:
            func(node)
        elif name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6',):
            self.process_heading(node)
        elif name in ('ol', 'ul',):
            self.process_list(node)
        else:
            raise MoinMoin.error.ConvertError("Don't support %s element" % name)

    def process_br(self, node):
            self.text.append('\n') # without this, std multi-line text below some heading misses a whitespace
                                   # when it gets merged to float text, like word word wordword word word
        
    def visit_node_list_element_only(self, node):
        for i in node:
            if i.nodeType == Node.ELEMENT_NODE:
                self.visit_element(i)

    def node_list_text_only(self, nodelist):
        result = []
        for i in nodelist:
            if i.nodeType == Node.TEXT_NODE:
                result.append(i.data)
            else:
                result.extend(self.node_list_text_only(i.childNodes))
        return "".join(result)

    def visit_text(self, node):
        self.text.append(node.data)

    def process_dl(self, node):
        self.depth += 1
        indent = " " * self.depth
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                if i.localName == 'dt':
                    self.text.append(indent)
                    text = self.node_list_text_only(i.childNodes)
                    self.text.append(text.replace("\n", " "))
                elif i.localName == 'dd':
                    self.text.append(":: ")
                    self.process_list_item(i)
                else:
                    raise MoinMoin.error.ConvertError("Illegal list element %s" % i.localName)
        if self.depth == 1:
            self.text.append("\n")
        self.depth -= 1

    def process_heading(self, node):
        text = self.node_list_text_only(node.childNodes).strip()
        if text:
            depth = int(node.localName[1]) - 1
            hstr = "=" * depth
            self.text.append(self.new_line)
            self.text.append("%s %s %s" % (hstr, text.replace("\n", " "), hstr))
            self.text.append(self.new_line)

    def _get_list_item_markup(self, list, listitem):
        markup = " " * self.depth
        type = None
        if list.localName == 'ol':
            if list.hasAttribute("type"):
                type = list.getAttribute("type")
            else:
                type = "1"
            markup = "%s%s. " % (markup, type)
        else:
            class_ = listitem.getAttribute("class")
            if class_ == "gap":
                markup = "\n" + markup
            style = listitem.getAttribute("style")
            if not re.match(u"list-style-type:\s*none", style, re.I):
                markup += "* "
        return markup

    def process_list(self, node):
        self.depth += 1
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                name = i.localName
                if name == 'li':
                    self.text.append(self._get_list_item_markup(node, i))
                    self.process_list_item(i)
                elif name in ('ol', 'ul',):
                    self.process_list(i)
                elif name == 'dl':
                    self.process_dl(i)
                else:
                    raise MoinMoin.error.ConvertError("Illegal list element %s" % i.localName)
        if self.depth == 1:
            self.text.append("\n")
        self.depth -= 1

    def process_list_item(self, node):
        found = False
        for i in node.childNodes:
            name = i.localName
            if name == 'p':
                self.process_paragraph_item(i)
                self.text.append("\n")
                found = True
            elif name == 'pre':
                self.process_preformatted_item(i)
                found = True
            elif name in ('ol', 'ul',):
                self.process_list(i)
                found = True
            elif name == 'dl':
                self.process_dl(i)
                found = True
            elif name == 'table':
                self.process_table(i)
                found = True
            #else:
            #    self.process_inline(i)
                
        if not found:
            self.process_paragraph_item(node)
            self.text.append("\n")

    def process_blockquote(self, node):
        self.depth += 1
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                name = i.localName
                if name == 'p':
                    self.text.append(self.new_line)
                    self.text.append(" " * self.depth)
                    self.process_p(i)
                elif name == 'pre':
                    self.text.append(self.new_line)
                    self.text.append(" " * self.depth)
                    self.process_pre(i)
                elif name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6',):
                    self.process_heading(i)
                elif name in ('ol', 'ul',):
                    self.process_list(i)
                elif name == 'dl':
                    self.process_dl(i)
                elif name == 'img':
                    self.process_img(i)
                elif name == 'div':
                    self.visit_node_list_element_only(i.childNodes)
                elif name == 'blockquote':
                    self.process_blockquote(i)
                elif name in ('br',):
                    self.process_br(i)
                else:
                    raise MoinMoin.error.ConvertError("Don't support %s element" % name)
        self.depth -= 1

    def process_page(self, node):
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                self.visit_element(i)
            elif i.nodeType == Node.TEXT_NODE: # if this is missing, all std text under a headline is dropped!
                txt = i.data.strip()
                if txt:
                    self.text.append(txt)
            #we use <pre class="comment"> now, so this is currently unused:
            #elif i.nodeType == Node.COMMENT_NODE:
            #    self.text.append(i.data)
            #    self.text.append("\n")

    def process_inline(self, node):
        if node.nodeType == Node.TEXT_NODE:
            self.text.append(node.data.strip('\n'))
            return

        name = node.localName
        func = getattr(self, "process_" + name,  None)
        if func:
            func(node)
            return

        command_close = None
        if name in ('em', 'i',):
            command = "''"
        elif name in ('strong', 'b',):
            command = "'''"
        elif name == 'u':
            command = "__"
        elif name == 'big':
            command = "~+"
            command_close = "+~"
        elif name == 'small':
            command = "~-"
            command_close = "-~"
        elif name == 'strike':
            command = "--("
            command_close = ")--"
        elif name == 'sub':
            command = ",,"
        elif name == 'sup':
            command = "^"
        elif name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6',): # headers are not allowed here (e.g. inside a ul li),
            text = self.node_list_text_only(node.childNodes).strip() # but can be inserted via the editor
            self.text.append(text)                          # so we just drop the header markup and keep the text
            return
        else:
            raise MoinMoin.error.ConvertError("Don't support %s element" % name)
        
        self.text.append(command)
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                self.process_inline(i)
            elif i.nodeType == Node.TEXT_NODE:
                self.text.append(i.data.strip('\n'))
        if command_close:
            command = command_close
        self.text.append(command)

    def process_span(self, node):
        # ignore span tags - just descend
        for i in node.childNodes:
            self.process_inline(i)

    def process_div(self, node):
        # ignore div tags - just descend
        for i in node.childNodes:
            self.process_inline(i)

    def process_tt(self, node):
        text = self.node_list_text_only(node.childNodes).replace("\n", " ")
        if node.getAttribute("css") == "backtick":
            self.text.append("`%s`" % text)
        else:
            self.text.append("{{{%s}}}" % text)

    def process_hr(self, node):
        if node.hasAttribute("class"):
            class_ = node.getAttribute("class")
        else:
            class_ = "hr0"
        if class_.startswith("hr") and class_[2] in "123456":
            length = int(class_[2]) + 4
        else:
            length = 4
        self.text.extend([self.new_line, "-" * length, self.new_line])

    def process_p(self, node):
        self.process_paragraph_item(node)
        self.text.append("\n\n")

    def process_paragraph_item(self, node):
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                self.process_inline(i)
            elif i.nodeType == Node.TEXT_NODE:
                self.text.append(i.data.strip('\n'))

    def process_pre(self, node):
        self.process_preformatted_item(node)
        self.text.append("\n")

    def process_preformatted_item(self, node):
        if node.hasAttribute("class"):
            class_ = node.getAttribute("class")
        else:
            class_ = None
        if class_ == "comment": # we currently use this for stuff like ## or #acl
            for i in node.childNodes:
                if i.nodeType == Node.TEXT_NODE:
                    self.text.append(i.data)
                    #print "'%s'" % i.data
                elif i.localName == 'br':
                    self.text.append("\n")
                else:
                    pass
                    #print i.localName
        else:
            self.text.extend(["{{{", self.new_line])
            for i in node.childNodes:
                if i.nodeType == Node.TEXT_NODE:
                    self.text.append(i.data)
                    #print "'%s'" % i.data
                elif i.localName == 'br':
                    self.text.append("\n")
                else:
                    pass
                    #print i.localName
            self.text.append("}}}\n")

    _alignment = {"left" : "(",
                  "center" : ":",
                  "right" : ")",
                  "top" : "^",
                  "bottom" : "v"}

    def _check_length(self, value):
        try:
            int(value)
            return value + 'px'
        except ValueError:
            return value

    def _table_style(self, node):
        result = []
        if node.hasAttribute("bgcolor"):
            value = node.getAttribute("bgcolor")
            match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", value)
            if match:
                result.append('tablebgcolor="#%X%X%X"' %
                              (int(match.group(1)),
                               int(match.group(2)),
                               int(match.group(3))))
            else:
                result.append('tablebgcolor="%s"' % value)
        if node.hasAttribute("width"):
            value = node.getAttribute("width")
            result.append('tablewidth="%s"' % self._check_length(value))
        if node.hasAttribute("height"):
            value = node.getAttribute("height")
            result.append('tableheight="%s"' % self._check_length(value))
        if node.hasAttribute("style"):
            result.append('tablestyle="%s"' % node.getAttribute("style"))
        return "".join(result)

    def _row_style(self, node):
        result = []
        if node.hasAttribute("bgcolor"):
            value = node.getAttribute("bgcolor")
            match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", value)
            if match:
                result.append('rowbgcolor="#%X%X%X"' %
                              (int(match.group(1)),
                               int(match.group(2)),
                               int(match.group(3))))
            else:
                result.append('rowbgcolor="%s"' % value)
        if node.hasAttribute("style"):
            result.append('rowstyle="%s"' % node.getAttribute("style"))
        return "".join(result)

    def _cell_style(self, node):
        align = ""

        if node.hasAttribute("rowspan"):
            rowspan = ("|%s" % node.getAttribute("rowspan"))
        else:
            rowspan = ""

        if node.hasAttribute("colspan"):
            colspan = int(node.getAttribute("colspan"))
        else:
            colspan = 1

        spanning = rowspan or colspan > 1
        
        result = []

        if  node.hasAttribute("bgcolor"):
            value = node.getAttribute("bgcolor")
            match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", value)
            if match:
                result.append("#%X%X%X" % (int(match.group(1)),
                                           int(match.group(2)),
                                           int(match.group(3))))
            else:
                result.append('bgcolor="%s"' % value)
        if node.hasAttribute("align"):
            value = node.getAttribute("align")
            if not spanning or value != "center":
                # ignore "center" in spanning cells
                align += self._alignment.get(value, "")
        if node.hasAttribute("valign"):
            value = node.getAttribute("valign")
            if not spanning or value != "center":
                # ignore "center" in spanning cells
                align += self._alignment.get(value, "")
        if node.hasAttribute("width"):
            value = node.getAttribute("width")
            if value[-1] == "%":
                align += value
            else:
                result.append('width="%s"' % self._check_length(value))
        if node.hasAttribute("height"):
            value = node.getAttribute("height")
            result.append('height="%s"' % self._check_length(value))
        if node.hasAttribute("class"):
            result.append('class="%s"' % node.getAttribute("class"))
        if node.hasAttribute("id"):
            result.append('id="%s"' % node.getAttribute("id"))
        if node.hasAttribute("style"):
            result.append('style="%s"' % node.getAttribute("style"))
                
        if align:
            result[0:0] = "%s" % align
        result.append(rowspan)
        result = "".join(result)
        #print result
        return result

    def process_table(self, node, style=""):
        self.new_table = True
        style += self._table_style(node)
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                name = i.localName
                if name == 'tr':
                    self.process_table_record(i, style)
                    style = ""
                elif name == 'tbody':
                    self.process_table(i, style)
                elif name == 'caption':
                    self.process_caption(node, i, style)
                    style = ''
                else:
                    raise MoinMoin.error.ConvertError("Don't support %s element" % name)
            #else:
            #    raise MoinMoin.error.ConvertError("Unexpected node: %r" % i)
        self.text.append("\n")

    def process_caption(self, table, node, style=""):
        # get first row
        for i in table.childNodes:
            if i.localName == 'tbody':
                for i in i.childNodes:
                    if i.localName == 'tr':
                        break
                break
            elif i.localName == 'tr':
                break
        # count columns
        if i.localName == 'tr':
            colspan = 0
            for td in i.childNodes:
                if not td.nodeType == Node.ELEMENT_NODE:
                    continue
                span = td.getAttribute('colspan')
                try:
                    colspan += int(span)
                except ValueError:
                    colspan += 1
        else:
            colspan = 1
        text = self.node_list_text_only(node.childNodes).replace('\n', ' ').strip()
        if text:
            self.text.append("%s'''%s%s'''||\n" % ('||' * colspan, style, text))

    def process_table_data(self, node, style=""):
        if node.hasAttribute("colspan"):
            colspan = int(node.getAttribute("colspan"))
        else:
            colspan = 1
        self.text.append("||" * colspan)

        style += self._cell_style(node)
        if style:
            self.text.append("<%s>" % style)

        found = False
        for i in node.childNodes:
            name = i.localName
            if name == 'p':
                self.process_paragraph_item(i)
                self.text.append(self.white_space)
                found = True
        if not found:
            for i in node.childNodes:
                if i.nodeType == Node.ELEMENT_NODE:
                    self.process_inline(i)
                    found = True
                elif i.nodeType == Node.TEXT_NODE:
                    data = i.data.strip('\n')
                    if data:
                        found = True
                        self.text.append(data)
        if not found:
            self.text.append(" ")

    def process_table_record(self, node, style=""):
        if not self.new_table:
            self.text.append(" " * self.depth)
        else:
            self.new_table = False
        style += self._row_style(node)
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                name = i.localName
                if name == 'td':
                    self.process_table_data(i, style=style)
                    style = ""
                else:
                    raise MoinMoin.error.ConvertError("Don't support %s element" % name)
        self.text.append("||\n")

    def _unquote_url(self, url): # XXX is it necessary to have "yet another unquote function"?
        url = str(url)
        url = urllib.unquote(url)
        return unicode(url, 'utf-8', 'replace')

    def process_a(self, node):
        scriptname = self.request.getScriptname()
        if scriptname == "":
            scriptname = "/"
        href = self._unquote_url(node.attributes.get("href").nodeValue)
        title = class_ = interwikiname = None

        if node.attributes.has_key("title"):
            title = node.attributes.get("title").nodeValue
        if node.attributes.has_key("class"):
            class_ = node.attributes.get("class").nodeValue

        text = self.node_list_text_only(node.childNodes)
        text = text.replace("\n", " ").lstrip()

         # interwiki link
        if class_ == "interwiki":
            wikitag, wikiurl, wikitail, err = wikiutil.resolve_wiki(
                self.request, title + ":")
            if not err and href.startswith(wikiurl):
                pagename = href[len(wikiurl):].lstrip('/')
                interwikiname = "%s:%s" % (wikitag, pagename)
            else: 
                raise MoinMoin.error.ConvertError("Invalid InterWiki link: '%s'" % href)
        elif class_ == "badinterwiki" and title:
            pagename = href
            interwikiname = "%s:%s" % (title, href)
        if interwikiname and pagename == text: # XXX interwiki can be undefined here!? 
            self.text.append("%s" % interwikiname)
            return
        elif title == 'Self':
            self.text.append("[:%s:%s]" % (href, text))
            return
        elif interwikiname:
            self.text.append("[wiki:%s %s]" % (interwikiname, text))
            return
        
        # fix links generated by a broken copy & paste of gecko based browsers
        brokenness = '../../../..'
        if href.startswith(brokenness):
            href = href[len(brokenness):] # just strip it away!
        # TODO: IE pastes complete http://server/Page/SubPage as href and as text, too

        # Attachments
        if title and title.startswith("attachment:"):
            url = self._unquote_url(title[len("attachment:"):])
            if url != text:
                self.text.append("[%s %s]" % (title, text))
            else:
                self.text.extend([self.white_space, title, self.white_space])
        # wiki link
        elif href.startswith(scriptname):
            pagename = href[len(scriptname):].replace('_', ' ')
            pagename = pagename.lstrip('/')    # XXX temp fix for generated pagenames starting with /
            if text == pagename:
                self.text.append(wikiutil.pagelinkmarkup(pagename))
            # relative link /SubPage
            elif href.endswith(text):
                if pagename.startswith(self.pagename): # is this a subpage of us?
                    self.text.append(wikiutil.pagelinkmarkup(pagename[len(self.pagename):]))
                else:
                    self.text.append(wikiutil.pagelinkmarkup(pagename))
            # relative link ../
            elif href.endswith(text.lstrip("..").lstrip("/")):
                self.text.append(wikiutil.pagelinkmarkup(text))
            # labeled link
            else:
                self.text.append("[:%s:%s]" % (pagename, text))
        # mailto link
        elif href.startswith("mailto:"):
            if href[len("mailto:"):] == text:
                self.text.extend([self.white_space, text, self.white_space])
            else:
                self.text.append("[%s %s]" % (href, text))
        # simple link
        elif href == text:
            self.text.append("%s" % href)
        # imagelink
        elif text == "" and wikiutil.isPicture(href):
            self.text.append("[%s]" % href)
        # labeled link
        else:
            self.text.append("[%s %s]" % (href, text))

    def process_img(self, node):
        src = None
        if node.attributes.has_key("src"):
            src = self._unquote_url(node.attributes.get("src").nodeValue)
        title = None
        if node.attributes.has_key("title"):
            title = node.attributes.get("title").nodeValue
        alt = None
        if node.attributes.has_key("alt"):
            alt = node.attributes.get("alt").nodeValue

        # Attachment image
        if (title and title.startswith("attachment:") and
            wikiutil.isPicture(self._unquote_url(title[len("attachment:"):]))):
            self.text.extend([self.white_space,
                              self._unquote_url(title),
                              self.white_space])
        # Drawing image
        elif title and title.startswith("drawing:"):
            self.text.extend([self.white_space,
                              self._unquote_url(title),
                              self.white_space])
        # Smiley
        elif src and (self.request.cfg.url_prefix in src or '../' in src) and "img/" in src: # XXX this is dirty!
            filename = src.split("/")[-1]
            for name, data in config.smileys.iteritems():
                if data[3] == filename:
                    self.text.extend([self.white_space, name, self.white_space])
                    return
                else:
                    pass #print name, data, filename, alt
            raise MoinMoin.error.ConvertError("Unknown smiley icon '%s'" % filename)
        # Image URL
        elif src and src.startswith("http://") and wikiutil.isPicture(src):
            self.text.extend([self.white_space, src, self.white_space])
        else:
            raise MoinMoin.error.ConvertError("Strange image src: '%s'" % src)


def parse(text):
    text = u'<?xml version="1.0"?>%s%s' % (dtd, text)
    text = text.encode(config.charset)
    try:
        return xml.dom.minidom.parseString(text)
    except xml.parsers.expat.ExpatError, msg:
        raise MoinMoin.error.ConvertError('ExpatError: %s' % msg)

def convert(request, pagename, text):
    text = u"<page>%s</page>" % text
    tree = parse(text)
    strip_whitespace().do(tree)
    strip_break().do(tree)
    return convert_tree(request, pagename).do(tree)

