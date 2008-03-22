# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - XML Serialization

    @copyright: 2002 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

class Marshal:
    """ Serialize Python data structures to XML.

        XML_DECL is the standard XML declaration.

        The class attributes ROOT_CONTAINER (default "data") and
        ITEM_CONTAINER (default "item") can be overwritten by derived
        classes; if ROOT_CONTAINER is `None`, the usually generated
        container element is omitted, the same is true for ITEM_CONTAINER.

        PRIVATE_PREFIXES is a list of prefixes of tagnames that are
        treated as private, i.e. things that should not be serialized.
        Default is to omit all properties starting with an underscore.

        TAG_MAP is a translation table for tag names, and is empty by
        default. It can also be used to suppress certain properties by
        mapping a tag name to `None`.
    """

    # Convenience: Standard XML declaration
    XML_DECL = '<?xml version="1.0" encoding="utf-8"?>\n'

    # Container Tags
    ROOT_CONTAINER = "data"
    ITEM_CONTAINER = "item"

    # List of private prefixes
    PRIVATE_PREFIXES = ['_']

    # Translation map
    TAG_MAP = {}


    def __toXML(self, element, data):
        """ Recursive helper method that transforms an object to XML.

            Returns a list of strings, which constitute the XML document.
        """
        # map tag names
        if self.TAG_MAP:
            element = self.TAG_MAP.get(element, element)

        if element:
            for prefix in self.PRIVATE_PREFIXES:
                if element.startswith(prefix):
                    return ''
            content = ['<%s>' % element]
        else:
            content = []

        # Handle the different data types
        add_content = content.extend

        if data is None:
            content = "<none/>"

        elif isinstance(data, str):
            content = (data.replace("&", "&amp;") # Must be done first!
                           .replace("<", "&lt;")
                           .replace(">", "&gt;"))

        elif isinstance(data, dict):
            for key, value in data.items():
                add_content(self.__toXML(key, value))

        elif isinstance(data, (list, tuple)):
            for item in data:
                add_content(self.__toXML(self.ITEM_CONTAINER, item))

        elif hasattr(data, "toXML"):
            add_content([data.toXML()])

        elif hasattr(data, "__dict__"):
            add_content(self.__toXML(self.ROOT_CONTAINER, data.__dict__))

        else:
            content = (str(data).replace("&", "&amp;") # Must be done first!
                                .replace("<", "&lt;")
                                .replace(">", "&gt;"))

        # Close container element
        if isinstance(content, str):
            # No Whitespace
            if element:
                content = ['<%s>%s</%s>' % (element, content, element)]
            else:
                content = [content]
        elif element:
            # Whitespace
            content.append('</%s>' % element)

        return content


    def toXML(self):
        """ Transform an instance to an XML string.
        """
        return '\n'.join(self.__toXML(self.ROOT_CONTAINER, self.__dict__))

