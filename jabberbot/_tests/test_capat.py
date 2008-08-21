# -*- coding: utf-8 -*-

import py

try:
    from jabberbot import capat
except ImportError:
    py.test.skip("Skipping jabber bot tests - pyxmpp is not installed")

def test_ver_simple():
    # example values supplied by the XEP
    ident = (("client", "pc"), )
    feat = ("http://jabber.org/protocol/disco#info",
            "http://jabber.org/protocol/disco#items",
            "http://jabber.org/protocol/muc",
           )

    assert capat.generate_ver(ident, feat) == "8RovUdtOmiAjzj+xI7SK5BCw3A8="

def test_ver_complex():
    # this test should verify that ordering works properly
    ident = (("client", "animal"),
             ("client", "bear"), # type ordering after category ordering
             ("apples", "bar"),
             ("apple", "foo"), # "apples" starts with "apple"
                               # thus it's greater
            )
    feat = ()

    expected = capat.hash_new('sha1')
    expected.update("apple/foo<apples/bar<client/animal<client/bear<")
    expected = capat.base64.b64encode(expected.digest())
    assert capat.generate_ver(ident, feat) == expected

def test_xml():
    try:
        import pyxmpp.iq
    except ImportError:
        py.test.skip("pyxmpp needs to be installed for this test")

    x = pyxmpp.iq.Iq(stanza_type='result', stanza_id='disco1',
                     from_jid='romeo@montague.lit/orchard',
                     to_jid='juliet@capulet.lit/chamber')
    y = x.new_query(ns_uri='http://jabber.org/protocol/disco#info')
    z = y.newChild(None, 'identity', None)
    z.setProp('category', 'client')
    z.setProp('type', 'pc')
    y.newChild(None, 'feature', None).setProp(
        'var', 'http://jabber.org/protocol/disco#info')
    y.newChild(None, 'feature', None).setProp(
        'var', 'http://jabber.org/protocol/disco#items')
    y.newChild(None, 'feature', None).setProp(
        'var', 'http://jabber.org/protocol/muc')

    assert capat.hash_iq(x) == "8RovUdtOmiAjzj+xI7SK5BCw3A8="
    # hash value taken from `test_ver_simple`

