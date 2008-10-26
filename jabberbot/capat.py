# -*- coding: utf-8 -*-

"""
    MoinMoin - Entity Capabilities (XEP-0115) implementation

    Enables Jabber/XMPP clients to save bandwidth by caching
    information about extensions supported by various client
    implementations.

    @copyright: 2007 by Robert Lehmann <lehmannro@gmail.com>
                2008 by Bolesław Kulbabiński <bolekk@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import base64
import itertools
from MoinMoin.support.python_compatibility import hash_new
from pyxmpp.presence import Presence

HASHALIASES = { # IANA Hash Function Textual Names Registry
                # to `hashlib.new` mapping
    'sha-1': 'sha1',
    'sha-224': 'sha224',
    'sha-256': 'sha256',
    'sha-384': 'sha384',
    'sha-512': 'sha512',
    'md5': 'md5',
    'md2': 'md2',
}


def generate_ver(identities, features, algo='sha-1'):
    """Generate the 'ver' attribute according to XEP-0115.

    See http://www.xmpp.org/extensions/xep-0115.html#ver

    @param identities: a number of (category, type) identity pairs
    @param algo: optional algo attribute with IANA aliasing

    @type identities: iterable of 2-tuples of strings
    @type features: iterable of strings
    @type algo: string (IANA Hash Function Textual Name)
    """

    # only IANA aliases are supported
    if algo not in HASHALIASES:
        raise ValueError("undefined hash algorithm")
    algo = hash_new(HASHALIASES[algo])

    ident = list(identities)
    # default sorting already considers both, category and type
    ident.sort()
    ident = ['%s/%s' % (idcat, idtype) for idcat, idtype in ident]

    feat = list(features)
    # strings (byte arrays) are ordered by i;octet by default
    feat.sort()

    s = '<'.join(itertools.chain(ident, feat, ('', )))
    # the trailing empty string adds a trailing '<' to the result
    algo.update(s)
    s = base64.b64encode(algo.digest())

    return s

def hash_iq(stanza, algo='sha-1'):
    """Search an <Iq/> entity for features/identities and generate a
    'ver' attribute hash.

    @type stanza: pyxmpp.iq.Iq
    """
    stanza = iter(stanza.get_query())
    stanza.next() # drop first item: whole query

    feat = []
    ident = []

    # traverse all child nodes
    for item in stanza:
        if item.name == 'identity':
            ident.append((item.prop('category'), item.prop('type')))
        elif item.name == 'feature':
            feat.append(item.prop('var'))

    return generate_ver(ident, feat, algo)

# <identity /> and <feature /> attributes
IDENT = (('category', 'client'),
         ('type', 'bot'))
FEAT = ('http://jabber.org/protocol/disco#info',
        'jabber:x:data') # data forms
NODE = "http://moinmo.in/#1.7"

def create_presence(jid):
    """ Creates a presence stanza (as described in XEP-0115)

    @param jid: bot's jabber ID
    """
    pres = Presence(from_jid=jid)

    c = pres.add_new_content('http://jabber.org/protocol/caps', 'c')
    c.setProp('node', NODE)

    ver = generate_ver(IDENT, FEAT)
    c.setProp('ver', ver)

    return pres

def create_response(disco_query):
    """ Creates an <Iq /> tag as a response to a service discovery query

    @param disco_query: received query
    """
    response = disco_query.make_result_response()
    query = response.new_query(ns_uri='http://jabber.org/protocol/disco#info')

    ident = query.newChild(None, 'identity', None)
    for item in IDENT:
        ident.setProp(item[0], item[1])

    for item in FEAT:
        query.newChild(None, 'feature', None).setProp('var', item)

    return response

