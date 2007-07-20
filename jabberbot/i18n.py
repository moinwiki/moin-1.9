# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber bot i18n routines

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

translations = None

def getText(original, lang="en"):
    global translations

    if not translations:
        init_i18n()

    try:
        return translations[lang][original]
    except KeyError:
        return original

def init_i18n():
    global translations
    translations = {'en': {}}
