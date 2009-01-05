"""
    werkzeug.contrib.testtools
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This Module implements a extended wrappers for simplified Testing

    `TestResponse`
        a response wrapper wich adds various cached attributes for
        simplified assertions on various contenttypes


    :copyright: 2007 by Ronny Pfannschmidt.
    :license: BSD, see LICENSE for more details.
"""
from werkzeug import Response, cached_property, import_string


class ContentAccessors(object):
    """
    A mixin class for response objects that provides a couple of useful
    accessors for unittesting.
    """

    def xml(self):
        """Get an etree if possible."""
        if 'xml' not in self.mimetype:
            raise AttributeError(
                'Not a XML response (Content-Type: %s)'
                % self.mimetype)
        for module in ['xml.etree.ElementTree', 'ElementTree',
                       'elementtree.ElementTree']:
            etree = import_string(module, silent=True)
            if etree is not None:
                return etree.XML(self.body)
        raise RuntimeError('You must have ElementTree installed '
                           'to use TestResponse.xml')
    xml = cached_property(xml)

    def lxml(self):
        """Get an lxml etree if possible."""
        if ('html' not in self.mimetype and 'xml' not in self.mimetype):
            raise AttributeError('Not an HTML/XML response')
        from lxml import etree
        try:
            from lxml.html import fromstring
        except ImportError:
            fromstring = etree.HTML
        if self.mimetype=='text/html':
            return fromstring(self.data)
        return etree.XML(self.data)
    lxml = cached_property(lxml)

    def json(self):
        """Get the result of simplejson.loads if possible."""
        if 'json' not in self.mimetype:
            raise AttributeError('Not a JSON response')
        from simplejson import loads
        return loads(self.data)
    json = cached_property(json)


class TestResponse(Response, ContentAccessors):
    """Pass this to `werkzeug.test.Client` for easier unittesting."""
