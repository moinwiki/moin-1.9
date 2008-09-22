# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - XML Utilities

    @copyright: 2001 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from xml.sax import saxutils
from MoinMoin import config


class XMLGenerator(saxutils.XMLGenerator):
    default_xmlns = {}

    def __init__(self, out):
        saxutils.XMLGenerator.__init__(self, out=out, encoding=config.charset)
        self.xmlns = self.default_xmlns

    def _build_tag(self, tag):
        if type(tag) == type(""):
            qname = tag
            tag = (None, tag)
        else:
            qname = "%s:%s" % tag
            tag = (self.xmlns[tag[0]], tag[1])
        return tag, qname

    def startNode(self, tag, attr={}):
        tag, qname = self._build_tag(tag)
        self.startElementNS(tag, qname, attr)

    def endNode(self, tag):
        tag, qname = self._build_tag(tag)
        self.endElementNS(tag, qname)

    def simpleNode(self, tag, value, attr={}):
        self.startNode(tag, attr)
        if value:
            self.characters(value)
        self.endNode(tag)

    def startDocument(self):
        saxutils.XMLGenerator.startDocument(self)
        for prefix, uri in self.xmlns.items():
            self.startPrefixMapping(prefix or None, uri)

    def endDocument(self):
        for prefix in self.xmlns:
            self.endPrefixMapping(prefix or None)
        saxutils.XMLGenerator.endDocument(self)


class RssGenerator(XMLGenerator):
    default_xmlns = {
        None:       "http://purl.org/rss/1.0/",
        'rdf':      "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        'xlink':    "http://www.w3.org/1999/xlink",
        'dc':       "http://purl.org/dc/elements/1.1/",
        'wiki':     "http://purl.org/rss/1.0/modules/wiki/",
    }

    def __init__(self, out):
        XMLGenerator.__init__(self, out=out)

    def startDocument(self):
        XMLGenerator.startDocument(self)
        self.startElementNS((self.xmlns['rdf'], 'RDF'), 'rdf:RDF', {})

    def endDocument(self):
        self.endElementNS((self.xmlns['rdf'], 'RDF'), 'rdf:RDF')
        XMLGenerator.endDocument(self)

