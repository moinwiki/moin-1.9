#!/usr/bin/env python
"""
   links the .po files to the current versions in the wiki.
   should be done before updating them with new strings
"""

import sys, os
sys.path.insert(0, '../..')
from MoinMoin import wikiutil

langs = 'da de es fi fr hu it ja ko nb nl pl ru sr vi zh zh-tw'.split()
broken_langs = 'hr pt sv'.split()
nonwiki_langs = 'he en'

data_dir = '/org/de.wikiwikiweb.moinmaster/data'

for lang in langs + broken_langs:
    langdir = os.path.join(data_dir, 'pages', wikiutil.quoteWikinameFS('MoinI18n/%s' % lang))
    pofn = lang.replace('-', '_') + '.po'
    if lang in broken_langs:
        langdir += '(2d)FIXME'
        pofn += '_'
    currentfn = os.path.join(langdir, 'current')
    current = open(currentfn, 'r').read().strip()
    wikifn = os.path.join(langdir, 'revisions', current)
    if os.path.exists(pofn):
        os.remove(pofn)
    os.symlink(wikifn, pofn)
    print "ln -s %s %s" % (wikifn, pofn)

