# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - HTML Widgets

    @copyright: 2003 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil

# sort attributes or not? (set to 1 by unit tests)
_SORT_ATTRS = 0


#############################################################################
### Base Classes
#############################################################################

class Text:
    """ A text node which will be escaped.
    """
    def __init__(self, text):
        self.text = text

    def __unicode__(self):
        return wikiutil.escape(self.text)


class Raw:
    """ Raw HTML code.
    """
    def __init__(self, markup):
        self.markup = markup

    def __unicode__(self):
        return self.markup


class Element:
    """ Abstract base class for HTML elements.
    """

    _ATTRS = {
    }
    _DEFAULT_ATTRS = {
    }
    _BOOL_ATTRS = {
        'checked': None,
        'compact': None,
        'defer': None,
        'disabled': None,
        'ismap': None,
        'multiple': None,
        'nohref': None,
        'noshade': None,
        'nowrap': None,
        'readonly': None,
        'selected': None,
    }

    def __init__(self, **kw):
        for key in kw:
            key = key.lower()
            if key not in self._ATTRS:
                raise AttributeError(
                    "Invalid HTML attribute %r for tag <%s>" % (
                        key, self.tagname()))

        self.attrs = self._DEFAULT_ATTRS.copy()
        self.attrs.update(kw)

    def tagname(self):
        return self.__class__.__name__.lower()

    def _openingtag(self):
        result = [self.tagname()]
        attrs = self.attrs.items()
        if _SORT_ATTRS:
            attrs.sort()
        for key, val in attrs:
            key = key.lower()
            if key in self._BOOL_ATTRS:
                if val:
                    result.append(key)
            else:
                result.append(u'%s="%s"' % (key, wikiutil.escape(val, 1)))
        return ' '.join(result)

    def __unicode__(self):
        raise NotImplementedError


class EmptyElement(Element):
    """ HTML elements with an empty content model.
    """

    def __unicode__(self):
        return u"<%s>" % self._openingtag()


class CompositeElement(Element):
    """ HTML elements with content.
    """

    def __init__(self, **kw):
        Element.__init__(self, **kw)
        self.children = []

    def append(self, child):
        """ Append child """
        self.children.append(child)
        return self

    def extend(self, children):
        for child in children:
            self.append(child)
        return self

    def __unicode__(self):
        childout = []
        for c in self.children:
            co = unicode(c)
            childout.append(co)
        return "<%s>%s</%s>" % (
            self._openingtag(),
            u''.join(childout),
            self.tagname(),
        )


#############################################################################
### HTML Elements
#############################################################################


class A(CompositeElement):
    "anchor"
    _ATTRS = {
        'accesskey': None,
        'charset': None,
        'class': None,
        'coords': None,
        'href': None,
        'hreflang': None,
        'name': None,
        'onblur': None,
        'onfocus': None,
        'rel': None,
        'rev': None,
        'shape': None,
        'tabindex': None,
        'type': None,
    }

class ABBR(CompositeElement):
    "abbreviated form (e.g., WWW, HTTP, etc.)"
    _ATTRS = {
        'class': None,
    }

class ACRONYM(CompositeElement):
    "acronyms"
    _ATTRS = {
        'class': None,
    }

class ADDRESS(CompositeElement):
    "information on author"
    _ATTRS = {
        'class': None,
    }

class AREA(EmptyElement):
    "client-side image map area"
    _ATTRS = {
        'alt': None,
        'class': None,
        'href': None,
        'shape': None,
    }

class B(CompositeElement):
    "bold text style"
    _ATTRS = {
        'class': None,
    }

class BASE(EmptyElement):
    "document base URI"
    _ATTRS = {
    }

class BDO(CompositeElement):
    "I18N BiDi over-ride"
    _ATTRS = {
        'class': None,
    }

class BIG(CompositeElement):
    "large text style"
    _ATTRS = {
        'class': None,
    }

class BLOCKQUOTE(CompositeElement):
    "long quotation"
    _ATTRS = {
        'class': None,
    }

class BODY(CompositeElement):
    "document body"
    _ATTRS = {
        'alink': None,
        'background': None,
        'bgcolor': None,
        'class': None,
        'link': None,
        'onload': None,
        'onunload': None,
        'text': None,
        'vlink': None,
    }

class BR(EmptyElement):
    "forced line break"
    _ATTRS = {
        'class': None,
    }

class BUTTON(CompositeElement):
    "push button"
    _ATTRS = {
        'class': None,
    }

class CAPTION(CompositeElement):
    "table caption"
    _ATTRS = {
        'class': None,
    }

class CITE(CompositeElement):
    "citation"
    _ATTRS = {
        'class': None,
    }

class CODE(CompositeElement):
    "computer code fragment"
    _ATTRS = {
        'class': None,
    }

class DD(CompositeElement):
    "definition description"
    _ATTRS = {
        'class': None,
    }

class DEL(CompositeElement):
    "deleted text"
    _ATTRS = {
        'class': None,
    }

class DFN(CompositeElement):
    "instance definition"
    _ATTRS = {
        'class': None,
    }

class DIV(CompositeElement):
    "generic language/style container"
    _ATTRS = {
        'id': None,
        'class': None,
    }

class DL(CompositeElement):
    "definition list"
    _ATTRS = {
        'class': None,
    }

class DT(CompositeElement):
    "definition term"
    _ATTRS = {
        'class': None,
    }

class EM(CompositeElement):
    "emphasis"
    _ATTRS = {
        'class': None,
    }

class FORM(CompositeElement):
    "interactive form"
    _ATTRS = {
        'accept': None,
        'action': None,
        'charset': None,
        'class': None,
        'enctype': None,
        'method': None,
        'name': None,
        'onreset': None,
        'onsubmit': None,
        'target': None,
    }
    _DEFAULT_ATTRS = {
        'method': 'POST',
    }

class H1(CompositeElement):
    "heading"
    _ATTRS = {
        'class': None,
    }

class H2(CompositeElement):
    "heading"
    _ATTRS = {
        'class': None,
    }

class H3(CompositeElement):
    "heading"
    _ATTRS = {
        'class': None,
    }

class H4(CompositeElement):
    "heading"
    _ATTRS = {
        'class': None,
    }

class H5(CompositeElement):
    "heading"
    _ATTRS = {
        'class': None,
    }

class H6(CompositeElement):
    "heading"
    _ATTRS = {
        'class': None,
    }

class HEAD(CompositeElement):
    "document head"
    _ATTRS = {
    }

class HR(EmptyElement):
    "horizontal rule"
    _ATTRS = {
        'class': None,
    }

class HTML(CompositeElement):
    "document root element"
    _ATTRS = {
        'version': None,
    }

class I(CompositeElement):
    "italic text style"
    _ATTRS = {
        'class': None,
    }

class IFRAME(CompositeElement):
    "inline subwindow"
    _ATTRS = {
        'class': None,
    }

class IMG(EmptyElement):
    "embedded image"
    _ATTRS = {
        'align': None,
        'alt': None,
        'border': None,
        'class': None,
        'vspace': None,
    }

class INPUT(EmptyElement):
    "form control"
    _ATTRS = {
        'accesskey': None,
        'align': None,
        'alt': None,
        'accept': None,
        'checked': None,
        'class': None,
        'disabled': None,
        'id': None,
        'ismap': None,
        'maxlength': None,
        'name': None,
        'onblur': None,
        'onchange': None,
        'onfocus': None,
        'onselect': None,
        'readonly': None,
        'size': None,
        'src': None,
        'tabindex': None,
        'type': None,
        'usemap': None,
        'value': None,
    }

class INS(CompositeElement):
    "inserted text"
    _ATTRS = {
        'class': None,
    }

class KBD(CompositeElement):
    "text to be entered by the user"
    _ATTRS = {
        'class': None,
    }

class LABEL(CompositeElement):
    "form field label text"
    _ATTRS = {
        'class': None,
        'for_': None,
    }

    def _openingtag(self):
        result = [self.tagname()]
        attrs = self.attrs.items()
        if _SORT_ATTRS:
            attrs.sort()
        for key, val in attrs:
            key = key.lower()
            if key == 'for_':
                key = 'for'
            if key in self._BOOL_ATTRS:
                if val:
                    result.append(key)
            else:
                result.append(u'%s="%s"' % (key, wikiutil.escape(val, 1)))
        return ' '.join(result)


class LI(CompositeElement):
    "list item"
    _ATTRS = {
        'class': None,
    }

class LINK(EmptyElement):
    "a media-independent link"
    _ATTRS = {
        'charset': None,
        'class': None,
        'href': None,
        'hreflang': None,
        'media': None,
        'rel': None,
        'rev': None,
        'target': None,
        'type': None,
    }

class MAP(CompositeElement):
    "client-side image map"
    _ATTRS = {
        'class': None,
    }

class META(EmptyElement):
    "generic metainformation"
    _ATTRS = {
    }

class NOSCRIPT(CompositeElement):
    "alternate content container for non script-based rendering"
    _ATTRS = {
        'class': None,
    }

class OL(CompositeElement):
    "ordered list"
    _ATTRS = {
        'class': None,
    }

class OPTGROUP(CompositeElement):
    "option group"
    _ATTRS = {
        'class': None,
    }

class OPTION(CompositeElement):
    "selectable choice"
    _ATTRS = {
        'class': None,
        'disabled': None,
        'label': None,
        'selected': None,
        'value': None,
    }

class P(CompositeElement):
    "paragraph"
    _ATTRS = {
        'class': None,
    }

class PRE(CompositeElement):
    "preformatted text"
    _ATTRS = {
        'class': None,
    }

class Q(CompositeElement):
    "short inline quotation"
    _ATTRS = {
        'class': None,
    }

class SAMP(CompositeElement):
    "sample program output, scripts, etc."
    _ATTRS = {
        'class': None,
    }

class SCRIPT(CompositeElement):
    "script statements"
    _ATTRS = {
    }

class SELECT(CompositeElement):
    "option selector"
    _ATTRS = {
        'class': None,
        'disabled': None,
        'multiple': None,
        'name': None,
        'onblur': None,
        'onchange': None,
        'onfocus': None,
        'size': None,
        'tabindex': None,
    }

class SMALL(CompositeElement):
    "small text style"
    _ATTRS = {
        'class': None,
    }

class SPAN(CompositeElement):
    "generic language/style container"
    _ATTRS = {
        'class': None,
    }

class STRONG(CompositeElement):
    "strong emphasis"
    _ATTRS = {
        'class': None,
    }

class STYLE(CompositeElement):
    "style info"
    _ATTRS = {
    }

class SUB(CompositeElement):
    "subscript"
    _ATTRS = {
        'class': None,
    }

class SUP(CompositeElement):
    "superscript"
    _ATTRS = {
        'class': None,
    }

class TABLE(CompositeElement):
    "table"
    _ATTRS = {
        'align': None,
        'bgcolor': None,
        'border': None,
        'cellpadding': None,
        'cellspacing': None,
        'class': None,
        'frame': None,
        'rules': None,
        'summary': None,
        'width': None,
    }

class TBODY(CompositeElement):
    "table body"
    _ATTRS = {
        'align': None,
        'class': None,
    }

class TD(CompositeElement):
    "table data cell"
    _ATTRS = {
        'abbr': None,
        'align': None,
        'class': None,
        'valign': None,
        'colspan': None,
        'rowspan': None,
    }

class TEXTAREA(CompositeElement):
    "multi-line text field"
    _ATTRS = {
        'class': None,
        'cols': None,
        'name': None,
        'rows': None,
    }

class TFOOT(CompositeElement):
    "table footer"
    _ATTRS = {
        'align': None,
        'class': None,
    }

class TH(CompositeElement):
    "table header cell"
    _ATTRS = {
        'abbr': None,
        'align': None,
        'class': None,
    }

class THEAD(CompositeElement):
    "table header"
    _ATTRS = {
        'align': None,
        'class': None,
    }

class TITLE(CompositeElement):
    "document title"
    _ATTRS = {
    }

class TR(CompositeElement):
    "table row"
    _ATTRS = {
        'align': None,
        'class': None,
    }

class TT(CompositeElement):
    "teletype or monospaced text style"
    _ATTRS = {
        'class': None,
    }

class UL(CompositeElement):
    "unordered list"
    _ATTRS = {
        'class': None,
    }

class VAR(CompositeElement):
    "instance of a variable or program argument"
    _ATTRS = {
        'class': None,
    }


#############################################################################
### Widgets
#############################################################################

#from MoinMoin.widget.base import Widget
#class FormWidget(Widget):
#    """ Widget to display data as an HTML form.
#
#        TODO: write code to combine the labels, data and HTML DOM to a complete form.
#
#        INCOMPLETE!!!
#    """
#
#    def __init__(self, request, **kw):
#        Widget.__init__(self, request)
#        self.form = form(**kw)
#
#    def render(self):
#        self.request.write(str(self.form))

