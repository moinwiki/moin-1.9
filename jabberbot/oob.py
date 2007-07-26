# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Out Of Band Data (XEP-066) implementation

    This is used by the xmpp thread to send URIs to clients
    in a structured manner.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from pyxmpp.message import Message
from pyxmpp.presence import Presence

def add_urls(stanza, data):
    """Adds a URL to a message or presence stanza

    Adds an <x> element qualified by the jabber:x:oob namespace
    to the stanza's payload

    @param stanza: message or presence stanza to add the URL info to
    @type stanza: pyxmpp.message.Message or pyxmpp.presence.Presence
    @param data: a list of dictionaries containing (url, description), as unicode
    @type data: list

    """
    if not (isinstance(stanza, Presence) or isinstance(stanza, Message)):
        raise TypeError("Stanza must be either of type Presence or Message!")

    for piece in data:
        x_elem = stanza.add_new_content(u"jabber:x:oob", u"x")
        url = x_elem.newChild(None, u"url", None)
        desc = x_elem.newChild(None, u"desc", None)
        url.addContent(piece['url'].encode("utf-8"))
        desc.addContent(piece['description'].encode("utf-8"))
