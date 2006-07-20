# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - site-wide configuration defaults (NOT per single wiki!)

    @copyright: 2005-2006 by Thomas Waldmann (MoinMoin:ThomasWaldmann)
    @license: GNU GPL, see COPYING for details.
"""
import re

# Threads flag - if you write a moin server that use threads, import
# config in the server and set this flag to True.
use_threads = False

# Charset - we support only 'utf-8'. While older encodings might work,
# we don't have the resources to test them, and there is no real
# benefit for the user. IMPORTANT: use only lowercase 'utf-8'!
charset = 'utf-8'

# Invalid characters - invisible characters that should not be in page
# names. Prevent user confusion and wiki abuse, e.g u'\u202aFrontPage'.
page_invalid_chars_regex = re.compile(
    ur"""
    \u0000 | # NULL

    # Bidi control characters
    \u202A | # LRE
    \u202B | # RLE
    \u202C | # PDF
    \u202D | # LRM
    \u202E   # RLM
    """,
    re.UNICODE | re.VERBOSE
    )

# Other stuff
umask = 0770
url_schemas = []

smileys = (r"X-( :D <:( :o :( :) B) :)) ;) /!\ <!> (!) :-? :\ >:> |) " +
           r":-( :-) B-) :-)) ;-) |-) (./) {OK} {X} {i} {1} {2} {3} {*} {o}").split()

# unicode: set the char types (upper, lower, digits, spaces)
from MoinMoin.util.chartypes import _chartypes
for key, val in _chartypes.items():
    if not vars().has_key(key):
        vars()[key] = val


